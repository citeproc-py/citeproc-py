
# http://sourceforge.net/mailarchive/message.php?msg_id=25355232

# http://dret.net/bibconvert/tex2unicode

#from citeproc import

import re
from lxml import objectify
from warnings import warn

from . import csl
from ..util import set_xml_catalog
from ..warnings import PyteWarning


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

    def __getattr__(self, name):
        return self[name]


class Reference(CustomDict):
    def __init__(self, key, type, **args):
        self.key = key
        self.type = type
        #required_or = [set(csl.VARIABLES)]
        optional = ({'uri', 'container_uri', 'contributor', 'date'} |
                    set(csl.VARIABLES))
        super().__init__(args, optional=optional)


class Name(CustomDict):
    def __init__(self, **args):
        if 'name' in args:
            required = {'name'}
            optional = {}
        else:
            required = {'given', 'family'}
            optional = {'dropping-particle', 'non-dropping-particle', 'suffix'}
        super().__init__(args, required, optional)

    def parts(self):
        return (self.get('given'), self.get('family'),
                self.get('dropping-particle'),
                self.get('non-dropping-particle'), self.get('suffix'))

    def given_initials(self):
        names = re.split(r'[- ]', self.given)
        return ' '.join('{}.'.format(name[0]) for name in names)


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
        super().__init__(args, required, optional)

    def __eq__(self, other):
        # TODO: for sorting
        raise NotImplementedError


class DateRange(DateBase):
    def __init__(self, **args):
        required = {'begin'}
        optional = {'end'}
        super().__init__(args, required, optional)

    def __eq__(self, other):
        # TODO: for sorting
        raise NotImplementedError


class Bibliography(list):
    def __init__(self, source, formatter):
        self.source = source
        self.formatter = formatter
        formatter.bibliography = self

    def cite(self, id):
        try:
            reference = self.source[id]
        except KeyError:
            warning = "Unknown reference ID '{}'".format(id)
            warn(warning, PyteWarning)
            return '[{}]'.format(warning)
        self.append(reference)
        return self.formatter.format_citation(reference)

    def bibliography(self, target):
        return self.formatter.format_bibliography(target)


class BibliographyFormatter(object):
    def __init__(self):
        pass

    def format_citation(self, reference):
        raise NotImplementedError

    def format_bibliography(self, target):
        raise NotImplementedError


class BibliographySource(dict):
    def add(self, entry):
        self[entry.key] = entry


class PseudoCSLDataXML(BibliographySource):
    def __init__(self, filename):
        set_xml_catalog()
        self.parser = objectify.makeparser(remove_comments=True,
                                           no_network=True)
        self.xml = objectify.parse(filename, self.parser)
        self.root = self.xml.getroot()
        for ref in self.root.ref:
            self.add(self.parse_reference(ref))

    def parse_reference(self, ref):
        key = str(ref.attrib['id'])
        authors = self.parse_authors(ref.author)
        issued = self.parse_date(ref.issued)
        if ref.type.text == 'article-journal':
            return Reference(key, type=csl.type.ARTICLE, author=authors,
                             title=ref.title.text,
                             container_title=ref.find('container-title').text,
                             issued=issued)
        elif ref.type.text == 'paper-conference':
            return Reference(key, type=csl.type.PAPER_CONFERENCE,
                             author=authors, title=ref.title.text,
                             container_title=ref.find('container-title').text,
                             issued=issued)
        else:
            raise NotImplementedError

    def parse_authors(self, author):
        authors = []
        for name in author.name:
            authors.append(self.parse_name(name))
        return authors

    def parse_name(self, name):
        return Name(given=name.given.text, family=name.family.text)

    def parse_date(self, date):
        return Date(year=date.year.text, month=date.month.text)


class MODS(BibliographySource):
    pass