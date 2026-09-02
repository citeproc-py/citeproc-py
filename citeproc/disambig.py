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
    disambiguate: int = 0           # <if disambiguate> activation level: 0 = off, N = fire first N blocks


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


_SUFFIX_CHARS = list('abcdefghijklmnopqrstuvwxyz')


def _merge_givens(a: list[int], b: list[int]) -> list[int]:
    """Merge two givens lists by taking the max at each position."""
    length = max(len(a), len(b))
    return [max(a[i] if i < len(a) else 0, b[i] if i < len(b) else 0)
            for i in range(length)]


def _compute_ikey(given: str | None, initialize_with: str | None) -> str:
    """Compute the initials key used for name frequency tracking.

    When initialize-with is set, produces the initials form (e.g. "J." for "John").
    When not set, returns the full given name as-is — the level-2 escalation path
    then handles the case where there's no abbreviation to show.
    """
    if not given:
        return ''
    if initialize_with is None:
        return given
    parts = given.replace('.', ' ').split()
    caps = [p[0] for p in parts if p and p[0].isupper()]
    if not caps:
        return given
    return initialize_with.join(caps) + initialize_with


def index_to_suffix(n: int) -> str:
    """Convert a zero-based integer index to a letter suffix.

    0 → "a", 1 → "b", ..., 25 → "z", 26 → "aa", 27 → "ab", ...
    """
    n += 1
    key = ''
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
    # When probing with a specific config, merge any globally-set givenname
    # levels from the item's stored _disambig so name-count probe renders
    # reflect all-names/primary-name expansion that was applied beforehand.
    effective_disambig = disambig
    if disambig is not None:
        stored = item.reference.get('_disambig')
        if stored and stored.givens:
            merged = _merge_givens(
                disambig.givens[0] if disambig.givens else [],
                stored.givens[0],
            )
            if merged != (disambig.givens[0] if disambig.givens else []):
                effective_disambig = AmbigConfig(
                    names=list(disambig.names),
                    givens=[merged],
                    maxvals=list(disambig.maxvals),
                    year_suffix=disambig.year_suffix,
                    disambiguate=disambig.disambiguate,
                )
    root.disambig_request = effective_disambig
    with _just_looking(root):
        result = layout.render_children(item)
    root.disambig_request = prev_request
    return str(result) if result is not None else ''


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
        extra_text_levels = self._index_disambiguate_conditions()
        layout = self.bib.style.root.citation.layout
        # Global givenname expansion must run first so that name-count probe
        # renders (in _dis_names) see the globally-expanded given names.
        self._dis_givens_global()
        for item_ids in self.ambigcites.values():
            if len(item_ids) < 2:
                continue
            still_clashing = list(item_ids)
            if add_names or (add_givenname and gd_rule == 'by-cite'):
                still_clashing = self._dis_names(item_ids)
            if add_year_suffix and still_clashing:
                render_groups: dict[str, list[str]] = {}
                for iid in still_clashing:
                    r = get_ambiguous_cite(self.registry[iid]['item'], layout,
                                          disambig=self.registry[iid]['disambig'])
                    render_groups.setdefault(r, []).append(iid)
                for group in render_groups.values():
                    self._dis_years(group)
                still_clashing = []  # year-suffix assigns unique suffixes to all remaining
            if extra_text_levels and still_clashing:
                self._dis_extra_text(still_clashing, extra_text_levels)

    def _dis_names(self, item_ids: list[str]) -> list[str]:
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
        prev_distinct = 1  # distinct render count at the last improvement step

        active_ids = list(item_ids)
        registered: dict[str, AmbigConfig] = {}

        while True:
            renders = {
                iid: get_ambiguous_cite(self.registry[iid]['item'], layout, disambig=base)
                for iid in active_ids
            }

            current_distinct = len(set(renders.values()))
            if current_distinct > prev_distinct:
                # improvement — partial capture (citeproc-js: captureStepToBase)
                # Only write the changed position so earlier over-incremented
                # levels don't pollute betterbase.
                betterbase.names[0] = base.names[0]
                betterbase.givens[0][gname] = base.givens[0][gname]
                improved = True
                prev_distinct = current_distinct

                # Register any items that are now uniquely rendered, snapshotting
                # betterbase at this moment so they don't inherit later expansion.
                render_counts = Counter(renders.values())
                for iid in list(active_ids):
                    if render_counts[renders[iid]] == 1:
                        old = self.registry[iid]['disambig']
                        registered[iid] = AmbigConfig(
                            names=list(betterbase.names),
                            givens=[_merge_givens(betterbase.givens[0], old.givens[0] if old.givens else [])],
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
                        givens=[_merge_givens(betterbase.givens[0], old.givens[0] if old.givens else [])],
                        maxvals=[names_max],
                        year_suffix=old.year_suffix,
                        disambiguate=old.disambiguate,
                    )
                    active_ids = []

                # After resolving some items, reset prev_distinct relative to
                # the remaining group so the next improvement is measured correctly.
                if active_ids:
                    prev_distinct = len(set(renders[iid] for iid in active_ids))

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
            return list(item_ids)

        for item_id in item_ids:
            if item_id in registered:
                new_config = registered[item_id]
            else:
                old = self.registry[item_id]['disambig']
                new_config = AmbigConfig(
                    names=list(betterbase.names),
                    givens=[_merge_givens(betterbase.givens[0], old.givens[0] if old.givens else [])],
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
        final_counts = Counter(final_renders.values())
        return [iid for iid in item_ids if final_counts[final_renders[iid]] > 1]

    def _index_disambiguate_conditions(self) -> int:
        """Stamp each <if disambiguate="true"> element with a sequential index.

        Returns the total count. Index 1 fires when disambiguate >= 1, index 2
        fires when disambiguate >= 2, etc. — allowing incremental extra-text
        expansion one block at a time.
        """
        # Index only within the citation layout — bibliography <if disambiguate>
        # elements use the default index (1) and fire whenever level >= 1.
        citation_layout = self.bib.style.root.citation.layout
        ns = citation_layout.nsmap
        csl_ns = ns.get('cs', 'http://purl.org/net/xbiblio/csl')
        count = 0
        for el in citation_layout.iter(f'{{{csl_ns}}}if', f'{{{csl_ns}}}else-if'):
            if el.get('disambiguate') == 'true':
                count += 1
                el.set('_disambig_index', str(count))
        return count

    def _dis_extra_text(self, item_ids: list[str], max_level: int):
        layout = self.bib.style.root.citation.layout
        still_clashing = list(item_ids)
        for level in range(1, max_level + 1):
            for iid in still_clashing:
                self.registry[iid]['disambig'].disambiguate = level
                self.bib.source[iid]['_disambig'] = self.registry[iid]['disambig']
            render_groups: dict[str, list[str]] = {}
            for iid in still_clashing:
                r = get_ambiguous_cite(self.registry[iid]['item'], layout,
                                      disambig=self.registry[iid]['disambig'])
                render_groups.setdefault(r, []).append(iid)
            still_clashing = [iid for grp in render_groups.values()
                              if len(grp) > 1 for iid in grp]
            if not still_clashing:
                break

    def _dis_years(self, item_ids: list[str]):
        # item_ids is already in bibliography sort order (bib.items order)
        for pos, item_id in enumerate(item_ids):
            self.registry[item_id]['disambig'].year_suffix = pos
            # Write the letter into the Reference so the renderer picks it up
            self.bib.source[item_id]['year_suffix'] = index_to_suffix(pos)

    def _dis_givens_global(self):
        """Expand given names globally for all-names and primary-name rules.

        Unlike by-cite expansion (which only fires when two cites actually clash),
        these rules expand given names whenever a family name appears more than once
        in the bibliography, regardless of whether the items would be confused.
        """
        citation = self.bib.style.root.citation
        if not citation.get_option('disambiguate-add-givenname'):
            return
        gd_rule = citation.get_option('givenname-disambiguation-rule')
        if gd_rule == 'by-cite':
            return

        primary_only = gd_rule.startswith('primary-name')
        with_initials_only = 'with-initials' in gd_rule

        # Get initialize-with from the first <name> element in the citation layout
        layout = citation.layout
        initialize_with: str | None = None
        for name_el in layout.findall('.//cs:name', layout.nsmap):
            iw = name_el.get('initialize-with')
            if iw is not None:
                initialize_with = iw
                break

        # Build namereg: rendered_family → {ikey: set_of_normalized_given_names}
        # A family name gets level 1 when it has >1 distinct ikey (distinct initials).
        # An ikey gets level 2 when it maps to >1 distinct given name (same initials clash).
        # pkey uses the rendered family form (ndp + family) so "dos Santos" ≠ "Santos".
        # skey is the normalized given name so "J. J." == "J.J." don't trigger expansion.
        namereg: dict[str, dict[str, set[str]]] = {}
        for entry in self.registry.values():
            item = entry['item']
            for var in self._name_vars:
                names_list = item.reference.get(var, [])
                for pos, name in enumerate(names_list):
                    if primary_only and pos > 0:
                        break
                    given, family, _dp, ndp, _suffix = name.parts()
                    if not family:
                        continue
                    pkey = ' '.join(n for n in (ndp, family) if n)
                    ikey = _compute_ikey(given, initialize_with)
                    skey = ' '.join(given.replace('.', ' ').split()).lower() if given else ''
                    namereg.setdefault(pkey, {}).setdefault(ikey, set()).add(skey)

        # Assign levels and write back to each item's AmbigConfig
        for item_id, entry in self.registry.items():
            item = entry['item']
            modified = False
            for var in self._name_vars:
                names_list = item.reference.get(var, [])
                if not names_list:
                    continue
                names_max = len(names_list)
                for pos, name in enumerate(names_list):
                    if primary_only and pos > 0:
                        break
                    given, family, _dp, ndp, _suffix = name.parts()
                    if not family:
                        continue
                    pkey = ' '.join(n for n in (ndp, family) if n)
                    if pkey not in namereg:
                        continue
                    ikeys_for_family = namereg[pkey]
                    ikey = _compute_ikey(given, initialize_with)

                    level = 0
                    if len(ikeys_for_family) > 1:
                        level = 1
                    if not with_initials_only:
                        if initialize_with is None and level > 0:
                            level = 2
                        elif ikey in ikeys_for_family and len(ikeys_for_family[ikey]) > 1:
                            level = 2

                    if level == 0:
                        continue

                    disambig = entry['disambig']
                    if not disambig.givens:
                        disambig.names = [1]
                        disambig.maxvals = [names_max]
                        disambig.givens = [[0] * names_max]
                    elif len(disambig.givens[0]) < names_max:
                        disambig.givens[0].extend([0] * (names_max - len(disambig.givens[0])))

                    if pos < len(disambig.givens[0]):
                        disambig.givens[0][pos] = max(disambig.givens[0][pos], level)
                        modified = True

            if modified:
                self.bib.source[item_id]['_disambig'] = entry['disambig']
