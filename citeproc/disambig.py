from __future__ import annotations

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
        self._build_registry()

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
        add_year_suffix = citation.get_option('disambiguate-add-year-suffix')
        for item_ids in self.ambigcites.values():
            if len(item_ids) < 2:
                continue
            resolved = False
            if add_names:
                resolved = self._dis_names(item_ids)
            if add_year_suffix and not resolved:
                self._dis_years(item_ids)

    def _dis_names(self, item_ids: list[str]) -> bool:
        """Expand name counts until all items are distinguishable.

        Returns True if all items in the group are now unique, False if some
        remain ambiguous (e.g. identical authors) and another mode is needed.
        """
        layout = self.bib.style.root.citation.layout
        betterbase = None
        prev_renders = None

        for count in range(2, 51):
            base = AmbigConfig(names=[count], givens=[], maxvals=[count])
            renders = {
                item_id: get_ambiguous_cite(self.registry[item_id]['item'], layout,
                                            disambig=base)
                for item_id in item_ids
            }

            if renders == prev_renders:
                break  # showing more names changes nothing; all names already shown

            if len(set(renders.values())) > 1:
                betterbase = base  # improvement — record minimum sufficient count

            if len(set(renders.values())) == len(item_ids):
                break  # fully resolved

            prev_renders = renders

        if betterbase is None:
            return False

        for item_id in item_ids:
            old = self.registry[item_id]['disambig']
            new_config = AmbigConfig(
                names=list(betterbase.names),
                givens=[],
                maxvals=list(betterbase.maxvals),
                year_suffix=old.year_suffix,
                disambiguate=old.disambiguate,
            )
            self.registry[item_id]['disambig'] = new_config
            self.bib.source[item_id]['_disambig'] = new_config

        final_renders = {
            item_id: get_ambiguous_cite(self.registry[item_id]['item'], layout,
                                        disambig=betterbase)
            for item_id in item_ids
        }
        return len(set(final_renders.values())) == len(item_ids)

    def _dis_years(self, item_ids: list[str]):
        # item_ids is already in bibliography sort order (bib.items order)
        for pos, item_id in enumerate(item_ids):
            self.registry[item_id]['disambig'].year_suffix = pos
            # Write the letter into the Reference so the renderer picks it up
            self.bib.source[item_id]['year_suffix'] = index_to_suffix(pos)
