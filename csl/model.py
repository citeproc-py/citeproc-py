
import re

from html.entities import codepoint2name

from lxml import etree


# Base class

class SomewhatObjectifiedElement(etree.ElementBase):
    nsmap = {'cs': 'http://purl.org/net/xbiblio/csl',
             'xml': 'http://www.w3.org/XML/1998/namespace'}

    # TODO: what about multiple instances of the same name?
    def __getattr__(self, name):
        return self.find('cs:' + name, self.nsmap)


class CitationStylesElement(SomewhatObjectifiedElement):
    _default_options = {# global options
                        'initialize-with-hyphen': 'true',
                        'page-range-format': None,
                        'demote-non-dropping-particle': 'display-and-sort',

                        # inheritable name(s) options
                        'and': None,
                        'delimiter-precedes-last': 'contextual',
                        'et-al-min': 0,
                        'et-al-use-first': 0,
                        'et-al-subsequent-min': 0,
                        'et-al-subsequent-use-first': 0,
                        'initialize-with': None,
                        'name-as-sort-order': None,
                        'sort-separator': ', ',

                        'name-form': 'long',
                        'name-delimiter': ', ',
                        'names-delimiter': ', '}

    def get_style(self):
        return self.getroottree().getroot()

    def xpath_search(self, expression):
        return self.xpath(expression, namespaces=self.nsmap)

    def get_option(self, name):
        return self.get(name, __class__._default_options[name])

    def get_citation(self):
        return self.get_style().citation

    def get_bibliography(self):
        return self.get_style().bibliography

    def get_macro(self, name):
        expression = "cs:macro[@name='{}'][1]".format(name)
        return self.get_style().xpath_search(expression)[0]

    def get_layout(self):
        return self.xpath_search('./ancestor::cs:layout[1]')[0]

    # TODO: Locale methods
    def get_term(self, name, form=None):
        for locale in self.get_style().locales:
            try:
                return locale.get_term(name, form)
            except IndexError: # TODO: create custom exception
                continue

    def get_date(self, form):
        for locale in self.get_style().locales:
            try:
                return locale.get_date(name)
            except IndexError:
                continue

    def get_locale_option(self, name):
        for locale in self.get_style().locales:
            try:
                return locale.get_option(name)
            except IndexError:
                continue


# Top level elements

class Style(CitationStylesElement):
    def set_locale_list(self, system_locale):
        from . import CitationStylesLocale

        def search_locale(locale):
            return self.xpath_search('./cs:locale[@xml:lang="{}"]'
                                     .format(locale))[0]

        self.locales = []
        try:
            self.locales.append(search_locale(system_locale))
        except IndexError:
            pass

        language = system_locale.split('-')[0]
        try:
            self.locales.append(search_locale(language))
        except IndexError:
            pass

        try:
            expr = './cs:locale[not(@xml:lang)]'
            self.locales.append(self.xpath_search(expr)[0])
        except IndexError:
            pass

        self.locales.append(CitationStylesLocale(system_locale).root)
        if system_locale != 'en-US':
            # TODO: add other locales with same locale
            self.locales.append(CitationStylesLocale('en-US').root)


class Locale(CitationStylesElement):
    _default_options = {'punctuation-in-quote': 'false'}

    def get_term(self, name, form=None):
        attributes = "@name='{}'".format(name)
        if form is not None:
            attributes += " and @form='{}'".format(form)
        else:
            attributes += " and not(@form)"
        expr = './cs:term[{}]'.format(attributes)
        return self.terms.xpath_search(expr)[0]

    def get_date(self, form):
        expr = "./cs:date[@form='{}']".format(form)
        return self.xpath_search(expr)[0]

    def get_option(self, name):
        options = self.find('cs:style-options', self.nsmap)
        return options.get(name, __class__._default_options[name])


class FormattingInstructions(object):
    def get_option(self, name):
        if name in self._default_options:
            return self.get(name, self._default_options[name])
        else:
            return self.get(name, self.get_style().get_option(name))

    def render(self, reference):
        raise NotImplementedError


class Citation(FormattingInstructions, CitationStylesElement):
    _default_options = {# disambiguation
                        'disambiguate-add-names': False,
                        'disambiguate-add-givenname': False,
                        'givenname-disambiguation-rule': 'all-names',
                        'disambiguate-add-year-suffix': False,

                        # citation collapsing
                        'collapse': None,
                        'year-suffix-delimiter': None,
                        'after-collapse-delimiter': None,

                        # note distance
                        'near-note-distance': 5}

    def render(self, reference):
        return self.layout.render_citation(reference)


class Bibliography(FormattingInstructions, CitationStylesElement):
    _default_options = {# whitespace
                        'hanging-indent': False,
                        'second-field-align': None,
                        'line-spacing': 1,
                        'entry-spacing': 1,

                        # reference grouping
                        'subsequent-author-substitute': None}

    def render(self, reference):
        return self.layout.render_bibliography(reference)


# Style behavior

class Formatted(object):
    def format(self, string):
        text = self.font_style(string)
        text = self.font_variant(text)
        text = self.font_weight(text)
        text = self.text_decoration(text)
        text = self.vertical_align(text)
        return text

    def font_style(self, text):
        font_style = self.get('font-style', 'normal')
        if font_style == 'normal':
            wrappers = '', ''
        elif font_style == 'italic':
            wrappers = '<i>', '</i>'
        elif font_style == 'oblique':
            wrappers = '<i>', '</i>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def font_variant(self, text):
        font_variant = self.get('font-variant', 'normal')
        if font_variant == 'normal':
            wrappers = '', ''
        elif font_variant == 'small-caps':
            wrappers = '<span style="font-variant:small-caps;">', '</span>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def font_weight(self, text):
        font_weight = self.get('font-weight', 'normal')
        if font_weight == 'normal':
            wrappers = '', ''
        elif font_weight == 'bold':
            wrappers = '<b>', '</b>'
        elif font_weight == 'light':
            wrappers = '<l>', '</l>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def text_decoration(self, text):
        text_decoration = self.get('text-decoration', 'none')
        if text_decoration == 'none':
            wrappers = '', ''
        elif text_decoration == 'underline':
            wrappers = '<u>', '</u>'
        return '{1}{0}{2}'.format(text, *wrappers)

    def vertical_align(self, text):
        vertical_align = self.get('vertical-align', 'baseline')
        if vertical_align == 'baseline':
            wrappers = '', ''
        elif vertical_align == 'sup':
            wrappers = '<sup>', '</sup>'
        elif vertical_align == 'sub':
            wrappers = '<sub>', '</sub>'
        return '{1}{0}{2}'.format(text, *wrappers)


class Affixed(object):
    def wrap(self, string):
        prefix = self.get('prefix', '')
        suffix = self.get('suffix', '')
        return prefix + string + suffix


class Delimited(object):
    def join(self, strings, default_delimiter=''):
        delimiter = self.get('delimiter', default_delimiter)
        return delimiter.join(strings)


class Displayed(object):
    pass


class Quoted(object):
    def quote(self, string):
        if self.get('quotes', False):
            return string


class StrippedPeriods(object):
    def strip_periods(self, string):
        if self.get('strip-periods', False):
            string = string.replace('.', '')
        return string


class TextCased(object):
    def case(self, text):
        text_case = self.get('text-case')
        if text_case is not None:
            if text_case == 'lowercase':
                text = text.lower()
            elif text_case == 'uppercase':
                text = text.upper()
            elif text_case == 'capitalize-first':
                text = text[0].capitalize() + text[1:]
            elif text_case == 'capitalize-all':
                text = text.title()
            elif text_case == 'title':
                text = text.title()
            elif text_case == 'sentence':
                text = text.capitalize()
        return text


# Locale

class Term(CitationStylesElement):
    @property
    def single(self):
        try:
            return self.find('cs:single', self.nsmap).text
        except AttributeError:
            return self.text

    @property
    def multiple(self):
        try:
            return self.find('cs:multiple', self.nsmap).text
        except AttributeError:
            return self.text


# Rendering elements

class Parent(object):
    def render_children(self, reference, *args, **kwargs):
        output = []
        for child in self.iterchildren():
            output.append(child.render(reference, *args, **kwargs))
        return output


class Sort(CitationStylesElement):
    def sort(self, references):
        raise NotImplementedError
        sort_keys = []
        for key in self.key:
            try:
                descending = key.attrib['sort'] == 'descending'
            except KeyError:
                descending = False
            # names-min, names-use-first
            sort_keys.append((key.variable, descending))


class Macro(CitationStylesElement, Parent, Delimited):
    def render(self, reference, context):
        # TODO: replace explicit context passing with xpath search for macro
        #       ancestor
        return self.join(self.render_children(reference, context=context))


class Layout(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def render_citation(self, references):
        # TODO: formatting
        self.repressed = {}
        out = []
        for ref in references:
            out.append(''.join(self.render_children(ref)))
            self.repressed = {}
        return self.format(self.wrap(self.join(out)))

    def render_bibliography(self, reference):
        return self.wrap(self.render_children(reference))


class Text(CitationStylesElement, Formatted, Affixed, TextCased,
           StrippedPeriods):
    def render(self, reference, context=None):
        if context is None:
            context = context or self

        if 'variable' in self.attrib:
            variable = self.get('variable')
            repressed = context.get_layout().repressed
            if self.tag in repressed and variable in repressed[self.tag]:
                return ''

            short = self.get('form') == 'short' # TODO: do something with this
            try:
                text = reference[variable.replace('-', '_')]
            except KeyError:
                return ''
        elif 'macro' in self.attrib:
            text = self.get_macro(self.get('macro')).render(reference, self)
        elif 'term' in self.attrib:
            form = self.get('form', 'long')
            plural = self.get('plural', 'false').lower() == 'true'
            if form == 'long':
                form = None
            term = self.get_term(self.get('term'), form)

            if plural:
                text = term.multiple
            else:
                text = term.single
        elif 'value' in self.attrib:
            text = self.get('value')

        # TODO: display, formatting, quotes, strip-periods, text-case
        return self.wrap(self.case(self.strip_periods(text)))


class Date(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def render(self, reference, context=None):
        variable = self.get('variable')
        output = []
        for part in self.iterchildren():
            output.append(part.render(reference, variable))
        return self.wrap(self.join(output))


class Date_Part(CitationStylesElement, Formatted, Affixed):
    def render(self, reference, variable):
        name = self.get('name')
        if name == 'day':
            form = self.get('form', 'numeric')
            if form == 'numeric':
                raise NotImplementedError
            elif form == 'numeric-leading-zeros':
                raise NotImplementedError
            elif form == 'ordinal':
                raise NotImplementedError
        elif name == 'month':
            form = self.get('form', 'long')
            strip_periods = self.get('form', False)
            if form == 'long':
                raise NotImplementedError
            elif form == 'short':
                raise NotImplementedError
            elif form == 'numeric':
                raise NotImplementedError
            elif form == 'numeric-leading-zeros':
                raise NotImplementedError
        elif name == 'year':
            form = self.get('form', 'long')
            if form == 'long':
                text = reference[variable.replace('-', '_')].year
            elif form == 'short':
                raise NotImplementedError

        return self.wrap(str(text))


class Number(CitationStylesElement, Formatted, Affixed, Displayed, TextCased):
    re_numeric = re.compile(r'^(\d+).*')

    def render(self, reference):
        variable = self.get('variable')
        form = self.get('form', 'numeric')
        try:
            number = self.re_numeric.match(reference[variable]).group(1)
            if form == 'numeric':
                text = str(number)
            elif form == 'ordinal':
                raise NotImplementedError
            elif form == 'long-ordinal':
                raise NotImplementedError
            elif form == 'roman':
                raise NotImplementedError
        except AttributeError:
            text = reference[variable]

        return self.wrap(self.format(self.case(text)))


class Names(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    def get_parent_delimiter(self, context=None):
        expr = './ancestor::*[self::cs:citation or self::cs:bibliography][1]'
        if context is None:
            context = self
        parent = context.xpath_search(expr)[0]
        return parent.get_option('names-delimiter')

    def substitute(self):
        expr = './cs:substitute[1]'
        try:
            result = self.xpath_search(expr)[0]
        except IndexError:
            result = None
        return result

    def render(self, reference, context=None):
        # if this instance substitutes another
        if context is None:
            context = self

        output = []
        for role in self.get('variable').split(' '):
            if role in reference:
                name_elem = context.name
                if name_elem is None:
                    name_elem = Name()
                    context.insert(0, name_elem)
                text = name_elem.render(reference, role, context=context)
                plural = len(reference[role]) > 1
                try:
                    text += context.label.render(reference, plural, role)
                except AttributeError:
                    pass
                output.append(text)

        if output:
            if isinstance(output[0], int):
                total = sum(output)
                text = str(total) if total > 0 else ''
            else:
                text = context.join(output, self.get_parent_delimiter(context))
        else:
            substitute = self.substitute()
            if substitute is not None:
                text = substitute.render(reference)
        try:
            return self.wrap(self.format(text))
        except NameError:
            return ''


class Name(CitationStylesElement, Formatted, Affixed, Delimited):
    def get_option(self, name, context=None):
        expr = './ancestor::*[self::cs:citation or self::cs:bibliography][1]'
        if context is None:
            context = self
        parent = context.xpath_search(expr)[0]
        if name in ('form', 'delimiter'):
            value = self.get(name, parent.get_option('name-' + name))
        else:
            value = self.get(name, parent.get_option(name))
            if name.startswith('et-al'):
                value = int(value)
            elif name in ('initialize-with-hyphen', ):
                value = value.lower() == 'true'
        return value

    def et_al(self):
        expr = './following-sibling::cs:et-al[1]'
        try:
            result = self.xpath_search(expr)[0].render()
        except IndexError:
            result = self.get_term('et-al').single
        return result

    def render(self, reference, variable, context=None):
        and_ = self.get_option('and', context)
        delimiter_precedes_last = self.get_option('delimiter-precedes-last',
                                                  context)

        et_al_min = self.get_option('et-al-min', context)
        et_al_use_first = self.get_option('et-al-use-first', context)
        et_al_subseq_min = self.get_option('et-al-subsequent-min', context)
        et_al_subseq_use_first = self.get_option('et-al-subsequent-use-first',
                                                 context)

        initialize_with = self.get_option('initialize-with', context)
        name_as_sort_order = self.get_option('name-as-sort-order', context)
        sort_separator = self.get_option('sort-separator', context)

        form = self.get('form', 'long')
        demote_ndp = self.get_option('demote-non-dropping-particle')

        def format_name_parts(given, family):
            for part in self.findall('cs:name-part', self.nsmap):
                given, family = part.format_part(given, family)
            return given, family

        names = reference.get(variable, [])

        if and_ == 'text':
            and_term = self.get_term('and').single
        elif and_ == 'symbol':
            and_term = '&' + codepoint2name[ord('&')] + ';'

        et_al = self.et_al()
        output = []
        if form == 'count':
            count = min(len(names), et_al_use_first)
            output.append(count)
            return sum(output)
        else:
            et_al_truncate = et_al_min and len(names) >= et_al_min
            if et_al_truncate:
                names = names[:et_al_use_first]
            for i, name in enumerate(names):
                given, family, dp, ndp, suffix = name.parts()

                if initialize_with is not None:
                    given = self.initialize(given, initialize_with, context)

                if form == 'long':
                    if (name_as_sort_order == 'all' or
                        (name_as_sort_order == 'first' and i == 0)):
                        if demote_ndp in ('never', 'sort-only'):
                            family = ' '.join([n for n in (ndp, family) if n])
                            given = ' '.join([n for n in (given, dp) if n])
                        else:
                            given = ' '.join([n for n in (given, dp, ndp) if n])

                        given, family = format_name_parts(given, family)
                        order = family, given, suffix
                        text = sort_separator.join([n for n in order if n])
                    else:
                        family = ' '.join([n for n in (dp, ndp, family) if n])
                        given, family = format_name_parts(given, family)
                        order = given, family, suffix
                        text = ' '.join([n for n in order if n])
                elif form == 'short':
                    given, family = format_name_parts(given, family)
                    text = family

                output.append(text)
            if et_al_truncate and et_al:
                if (delimiter_precedes_last == 'always' or
                    (delimiter_precedes_last == 'contextual' and
                     len(output) >= 2)):
                    output.append(et_al)
                    text = self.join(output, ', ')
                else:
                    text = self.join(output, ', ') + ' ' + et_al
            elif and_ is not None and len(output) > 1:
                text = self.join(output[:-1], ', ')
                if (delimiter_precedes_last == 'always' or
                    (delimiter_precedes_last == 'contextual' and
                     len(output) > 2)):
                        text = self.join([text, ''])
                else:
                    text += ' '
                text += '{} '.format(and_term) + output[-1]
            else:
                text = self.join(output, ', ')
            return self.wrap(self.format(text))

    def initialize(self, given, mark, context):
        if self.get_option('initialize-with-hyphen', context):
            hyphen_parts = given.split('-')
        else:
            hyphen_parts = [given.replace('-', ' ')]

        result_parts = []
        for hyphen_part in hyphen_parts:
            parts = hyphen_part.replace('.', ' ').split()
            hyphen_result = ''
            group = []
            for part in parts:
                if part[0].isupper():
                    group.append(part[0])
                else:
                    # don't initialize particles (which aren't capitalized)
                    hyphen_result += mark.join(group) + mark + ' ' + part + ' '
                    group = []
            hyphen_result += mark.join(group) + mark
            # remove double spaces
            hyphen_result = ' '.join(hyphen_result.split())
            result_parts.append(hyphen_result)
        return '-'.join(result_parts)


class Name_Part(CitationStylesElement, Formatted, Affixed, TextCased):
    def format_part(self, given, family):
        if self.get('name') == 'given':
            given = self.wrap(self.format(self.case(given)))
        elif self.get('name') == 'family':
            family = self.wrap(self.format(self.case(family)))
        return given, family


class Et_Al(CitationStylesElement, Formatted, Affixed):
    def render(self):
        variable = self.get('term', 'et-al')
        term = self.get_term('variable')
        if term:
            return self.wrap(self.format(text))
        else:
            return None


class Substitute(CitationStylesElement):
    def render(self, reference):
        for child in self.getchildren():
            if isinstance(child, Names) and child.name is None:
                names = self.xpath_search('./parent::cs:names[1]')[0]
                text = child.render(reference, context=names)
            else:
                text = child.render(reference)
            if text:
                self.add_to_repressed_list(child)
                break
        return text

    def add_to_repressed_list(self, child):
        layout = self.get_layout()
        tag_list = layout.repressed.get(child.tag, [])
        tag_list.append(child.get('variable'))
        layout.repressed[child.tag] = tag_list


class Label(CitationStylesElement, Formatted, Affixed, StrippedPeriods,
            TextCased):
    def render(self, reference, plural, variable=None):
        if variable is None:
            variable = self.get('variable')
        form = self.get('form', 'long')
        plural_option = self.get('plural', 'contextual')
        if form == 'long':
            term = self.get_term(variable)
        else:
            term = self.get_term(variable, form)

        if (plural_option == 'contextual' and plural or
            plural_option == 'always'):
            text = term.multiple
        else:
            text = term.single

        if text is None:
            return ''
        else:
            return self.wrap(self.format(self.case(self.strip_periods(text))))


class Group(CitationStylesElement, Parent, Formatted, Affixed, Delimited):
    # Note that cs:group implicitly acts as a conditional: cs:group and its
    # child elements are suppressed if
    #  a) at least one rendering element in cs:group calls a variable (either
    #     directly or via a macro), and
    #  b) all variables that are called are empty. This behavior exists to
    #     accommodate descriptive cs:text elements.
    def render(self, reference, context=None):
        return self.wrap(self.join(self.render_children(reference)))


class ConditionFailed(Exception):
    pass


class Choose(CitationStylesElement):
    def render(self, reference, context=None):
        try:
            return self.find('cs:if', self.nsmap).render(reference)
        except ConditionFailed:
            pass

        try:
            for else_if in self.find('cs:else-if', self.nsmap):
                try:
                    return else_if.render(reference)
                except ConditionFailed:
                    continue
        except AttributeError:
            pass

        try:
            return self.find('cs:else', self.nsmap).render(reference)
        except AttributeError or ConditionFailed:
            return ''


class If(CitationStylesElement, Parent):
    def render(self, reference, context=None):
        # TODO self.get('disambiguate')
        results = []
        if 'type' in self.attrib:
            results.append(self._type(reference))
        if 'variable' in self.attrib:
            results.append(self._variable(reference))
        if 'is-numeric' in self.attrib:
            results.append(self._is_numeric(reference))
        if 'is-uncertain-date' in self.attrib:
            results.append(self._is_uncertain_date(reference))
        if 'locator' in self.attrib:
            results.append(self._locator(reference))
        if 'position' in self.attrib:
            results.append(self._position(reference))

        # TODO: 'match' also applies to individual tests above!
        if self.get('match') == 'any':
            result = any(results)
        elif self.get('match') == 'none':
            result = not all(results)
        else:
            result = all(results)

        if not result:
            raise ConditionFailed

        return self.render_children(reference)

    def _type(self, reference):
        return reference.type in self.get('type').split(' ')

    def _variable(self, reference):
        return set(self.get('variable').split(' ')) <= set(reference.keys())

    def _is_numeric(self, reference):
        variable = self.get('is-numeric')
        return Number.re_numeric.match() is not None

    def _is_uncertain_date(self, reference):
        date_variable = self.get('is-uncertain-date')
        return reference[date_variable].get('circa', False)

    def _locator(self, reference):
        raise NotImplementedError

    def _position(self, reference):
        raise NotImplementedError


class Else_If(If):
    pass


class Else(CitationStylesElement, Parent):
    def render(self, reference, context=None):
        return self.render_children(reference)
