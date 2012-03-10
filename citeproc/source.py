
# http://sourceforge.net/mailarchive/message.php?msg_id=25355232

# http://dret.net/bibconvert/tex2unicode

from warnings import warn

from lxml import objectify

from . import VARIABLES


class CustomDict(dict):
    def __init__(self, args, required=set(), optional=set(), required_or=[]):
        passed_keywords = set(args.keys())
        missing = required - passed_keywords
        if missing:
            raise TypeError('The following required arguments are missing: ' +
                            ', '.join(missing))
        required_or_merged = set()
        for required_options in required_or:
            if not passed_keywords & required_options:
                raise TypeError('Require at least one of: ' +
                                ', '.join(required_options))
            required_or_merged |= required_options
        unsupported = passed_keywords - required - optional - required_or_merged
        if unsupported:
            cls_name = self.__class__.__name__
            warn('The following arguments for {} are '.format(cls_name) +
                 'unsupported: ' + ', '.join(unsupported))
        self.update(args)

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            raise VariableError


class Reference(CustomDict):
    def __init__(self, key, type, **args):
        self.key = key
        self.type = type
        #required_or = [set(csl.VARIABLES)]
        optional = ({'uri', 'container_uri', 'contributor', 'date'} |
                    set(VARIABLES))
        super().__init__(args, optional=optional)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.key)


class VariableError(Exception):
    pass


class Name(CustomDict):
    def __init__(self, **args):
        if 'name' in args:
            required = {'name'}
            optional = set()
        else:
            required = {'given', 'family'}
            optional = {'dropping-particle', 'non-dropping-particle', 'suffix'}
        super().__init__(args, required, optional)

    def parts(self):
        return (self.get('given'), self.get('family'),
                self.get('dropping-particle'),
                self.get('non-dropping-particle'), self.get('suffix'))


class DateBase(CustomDict):
    def __init__(self, args, required=set(), optional=set()):
        optional = {'circa'} | optional
        super().__init__(args, required, optional)
        # defaults
        if 'circa' not in self:
            self['circa'] = False


class Date(DateBase):
    def __init__(self, **args):
        required = {'year'}
        optional = {'month', 'day', 'season'}
        if 'day' in args and 'month' not in args:
            raise TypeError('When specifying the day, you should also specify '
                            'the month')
        args = {key: int(value) for key, value in args.items()}
        super().__init__(args, required, optional)

    def sort_key(self):
        year = self.year
        month = self.get('month', 0)
        day = self.get('day', 0)
        return '{:05}{:02}{:02}'.format(year + 10000, month, day)

    def is_nil(self):
        return (self.year == 0 and self.get('month', 0) == 0 and
                self.get('day', 0) == 0)


class DateRange(DateBase):
    def __init__(self, **args):
        required = {'begin'}
        optional = {'end'}
        super().__init__(args, required, optional)

    def sort_key(self):
        begin = self.begin.sort_key()
        end = self.get('end', Date(year=0)).sort_key()
        return begin + '-' + end

    def __eq__(self, other):
        # TODO: for sorting
        raise NotImplementedError


class Citation(CustomDict):
    def __init__(self, cites, **kwargs):
        for cite in cites:
            cite.citation = self
        self.cites = cites
        super().__init__(kwargs)

    def __repr__(self):
        cites = ', '.join([cite.key for cite in self.cites])
        return '{}({})'.format(self.__class__.__name__, cites)


class CitationItem(CustomDict):
    def __init__(self, key, bibliography=None, **args):
        self.key = key
        if bibliography:
            self._bibliography = bibliography
        optional = {'locator', 'prefix', 'suffix'}
        super().__init__(args, optional=optional)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.key)

    @property
    def reference(self):
        return self._bibliography.source[self.key]

    @property
    def number(self):
        return self._bibliography.items.index(self) + 1


class Locator(object):
    def __init__(self, label, identifier):
        self.label = label
        self.identifier = identifier


class Bibliography(object):
    def __init__(self, source, formatter):
        self.source = source
        self.formatter = formatter
        formatter.bibliography = self
        self.references = []

    def register(self, citation):
        for item in citation.items:
            self.references.append(item.reference)

    def cite(self, key):
        try:
            reference = self.source[key]
        except KeyError:
            warning = "Unknown reference ID '{}'".format(id)
            warn(warning)
            return '[{}]'.format(warning)
        self.register(reference)
        return self.formatter.format_citation(reference)

    def bibliography(self, target=None):
        return self.formatter.format_bibliography(target)


class BibliographySource(dict):
    def add(self, entry):
        self[entry.key] = entry
