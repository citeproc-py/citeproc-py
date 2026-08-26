from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class AmbigConfig:
    names: list[int]          # how many names to show per nameset
    givens: list[list[int]]   # given-name expansion level per name per nameset
                              # 0 = no given, 1 = initials, 2 = full given name
    maxvals: list[int]        # max available names per nameset
    year_suffix: int | None = None  # None = not assigned; 0 → "a", 1 → "b", ...
    disambiguate: bool = False      # whether <if disambiguate> should fire


def clone_ambig_config(config: AmbigConfig, oldconfig: AmbigConfig | None = None) -> AmbigConfig:
    """Clone an AmbigConfig.

    names/givens/maxvals come from config (the forward counter being incremented).
    year_suffix and disambiguate come from oldconfig if provided, preserving any
    state written by earlier disambiguation modes.
    """
    cloned = AmbigConfig(
        names=list(config.names),
        givens=[list(g) for g in config.givens],
        maxvals=list(config.maxvals),
        year_suffix=config.year_suffix,
        disambiguate=config.disambiguate,
    )
    if oldconfig is not None:
        cloned.year_suffix = oldconfig.year_suffix
        cloned.disambiguate = oldconfig.disambiguate
    return cloned


_SUFFIX_CHARS = list("abcdefghijklmnopqrstuvwxyz")


def index_to_suffix(n: int) -> str:
    """Convert a zero-based integer index to a letter suffix.

    0 → "a", 1 → "b", ..., 25 → "z", 26 → "aa", 27 → "ab", ...
    """
    n += 1
    key = ""
    while n:
        x = n % 26 or 26
        key = _SUFFIX_CHARS[x - 1] + key
        n = (n - x) // 26
    return key


@contextmanager
def _just_looking(style_root):
    """Suppress disambiguation-sensitive output during probe renders."""
    style_root.just_looking = True
    try:
        yield
    finally:
        style_root.just_looking = False


def get_ambiguous_cite(item, layout, disambig=None) -> str:
    """Probe-render a single citation item.

    When disambig is None, renders in baseline form (no disambiguation applied).
    The result is used as the ambig key for grouping. When disambig is an
    AmbigConfig, renders with those settings so the caller can test whether
    items have become distinguishable after a disambiguation step.
    """
    root = layout.get_root()
    layout.repressed = {}
    citation_element = layout.getparent()
    if citation_element.cites is None:
        citation_element.cites = []
    prev_request = root.disambig_request
    root.disambig_request = disambig
    with _just_looking(root):
        result = layout.render_children(item)
    root.disambig_request = prev_request
    return str(result) if result is not None else ""


class Disambiguation:
    def __init__(self, bib):
        self.bib = bib
        self.registry = {}      # str(item_id) → {'ambig': akey, 'disambig': AmbigConfig}
        self.ambigcites = {}    # akey → [str(item_id), ...]
        self._name_vars = self._collect_name_vars()
        self._build_registry()

    def _collect_name_vars(self) -> frozenset[str]:
        """Collect name variables from all <names> elements in the loaded style.

        Searching the full style tree (not just the citation layout) captures
        variables defined in macros. This is style-driven rather than based on
        a static CSL spec list, so it stays accurate as styles evolve.
        """
        style_root = self.bib.style.root
        name_vars: set[str] = set()
        for names_el in style_root.findall('.//cs:names', style_root.nsmap):
            for v in (names_el.get('variable') or '').split():
                name_vars.add(v)
        return frozenset(name_vars)

    def _build_registry(self):
        layout = self.bib.style.root.citation.layout
        for item in self.bib.items:
            item_id = str(item.key)
            akey = get_ambiguous_cite(item, layout)
            self.registry[item_id] = {
                'ambig': akey,
                'disambig': AmbigConfig(names=[], givens=[], maxvals=[]),
                'item': item,
            }
            if akey not in self.ambigcites:
                self.ambigcites[akey] = []
            if item_id not in self.ambigcites[akey]:
                self.ambigcites[akey].append(item_id)

    def run(self):
        citation = self.bib.style.root.citation
        add_names = citation.get_option('disambiguate-add-names')
        add_givenname = citation.get_option('disambiguate-add-givenname')
        gd_rule = citation.get_option('givenname-disambiguation-rule')
        add_year_suffix = citation.get_option('disambiguate-add-year-suffix')
        for item_ids in self.ambigcites.values():
            if len(item_ids) < 2:
                continue
            resolved = False
            if add_names or (add_givenname and gd_rule == 'by-cite'):
                resolved = self._dis_names(item_ids)
            if add_year_suffix and not resolved:
                self._dis_years(item_ids)

    def _dis_names(self, item_ids: list[str]) -> bool:
        """Expand name counts and given names using the citeproc-js incrementDisambig order.

        When disambiguate-add-givenname with by-cite is active, given name expansion
        is interleaved with name count expansion: the current author's given name is
        tried before the next author is revealed. givens_max=0 disables that
        dimension so only name count expansion runs.

        Returns True if all items in the group are now unique, False otherwise.
        """
        layout = self.bib.style.root.citation.layout
        citation = self.bib.style.root.citation
        add_names = citation.get_option('disambiguate-add-names')
        add_givenname = citation.get_option('disambiguate-add-givenname')
        gd_rule = citation.get_option('givenname-disambiguation-rule')
        givens_max = 2 if (add_givenname and gd_rule == 'by-cite') else 0

        # Max name count from actual item data (citeproc-js: maxNamesByItemId).
        # Clamped to 1: anonymous items (no names for any variable) must still
        # get a valid givens slot so the loop can run to exhaustion safely.
        names_max = max(
            max((len(self.registry[iid]['item'].reference.get(v, []))
                 for v in self._name_vars),
                default=0)
            for iid in item_ids
        )
        names_max = max(names_max, 1)

        # Pre-initialize base and betterbase with givens slots for all author
        # positions (citeproc-js: padBase — all levels start at 0)
        base = AmbigConfig(names=[1], givens=[[0] * names_max], maxvals=[names_max])
        betterbase = AmbigConfig(names=[1], givens=[[0] * names_max], maxvals=[names_max])
        improved = False
        gname = 0  # cursor: which author position we're currently expanding givens for

        active_ids = list(item_ids)
        registered: dict[str, AmbigConfig] = {}

        while True:
            renders = {
                iid: get_ambiguous_cite(self.registry[iid]['item'], layout, disambig=base)
                for iid in active_ids
            }

            if len(set(renders.values())) > 1:
                # improvement — partial capture (citeproc-js: captureStepToBase)
                # Only write the changed position so earlier over-incremented
                # levels don't pollute betterbase.
                betterbase.names[0] = base.names[0]
                betterbase.givens[0][gname] = base.givens[0][gname]
                improved = True

                # Register any items that are now uniquely rendered, snapshotting
                # betterbase at this moment so they don't inherit later expansion.
                render_counts = Counter(renders.values())
                for iid in list(active_ids):
                    if render_counts[renders[iid]] == 1:
                        old = self.registry[iid]['disambig']
                        registered[iid] = AmbigConfig(
                            names=list(betterbase.names),
                            givens=[list(betterbase.givens[0])],
                            maxvals=[names_max],
                            year_suffix=old.year_suffix,
                            disambiguate=old.disambiguate,
                        )
                        active_ids.remove(iid)

                # If one item remains it has no one left to clash with.
                if len(active_ids) == 1:
                    iid = active_ids[0]
                    old = self.registry[iid]['disambig']
                    registered[iid] = AmbigConfig(
                        names=list(betterbase.names),
                        givens=[list(betterbase.givens[0])],
                        maxvals=[names_max],
                        year_suffix=old.year_suffix,
                        disambiguate=old.disambiguate,
                    )
                    active_ids = []

            if not active_ids:
                break

            # incrementDisambig: priority order from citeproc-js
            if givens_max and base.givens[0][gname] < givens_max:
                # Step 1: expand given name for current author
                base.givens[0][gname] += 1
            elif add_names and base.names[0] < names_max:
                # Step 2: reveal next author, advance cursor to newly exposed position
                base.names[0] += 1
                gname += 1
            else:
                break  # all options exhausted

        if not improved:
            return False

        for item_id in item_ids:
            if item_id in registered:
                new_config = registered[item_id]
            else:
                old = self.registry[item_id]['disambig']
                new_config = AmbigConfig(
                    names=list(betterbase.names),
                    givens=[list(betterbase.givens[0])],
                    maxvals=[names_max],
                    year_suffix=old.year_suffix,
                    disambiguate=old.disambiguate,
                )
            self.registry[item_id]['disambig'] = new_config
            self.bib.source[item_id]['_disambig'] = new_config

        final_renders = {
            iid: get_ambiguous_cite(self.registry[iid]['item'], layout,
                                    disambig=self.registry[iid]['disambig'])
            for iid in item_ids
        }
        return len(set(final_renders.values())) == len(item_ids)

    def _dis_years(self, item_ids: list[str]):
        # item_ids is already in bibliography sort order (bib.items order)
        for pos, item_id in enumerate(item_ids):
            self.registry[item_id]['disambig'].year_suffix = pos
            # Write the letter into the Reference so the renderer picks it up
            self.bib.source[item_id]['year_suffix'] = index_to_suffix(pos)
