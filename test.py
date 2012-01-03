

import glob
import io
import json
import os
import sys
import traceback

from codecs import utf_8_encode
from functools import reduce

from pyte.bibliography.csl import CitationStylesStyle, NAMES, DATES, NUMBERS
from pyte.bibliography import Reference, Name, Date, DateRange
from pyte.bibliography import Citation, CitationItem, Locator
from pyte.bibliography.csl import CitationStylesBibliography


TESTS_VERSION = '71dfc1c91b3e'
#TESTS_VERSION = 'c26e5808a0f1'

TESTS_PATH = ('C:/Documents and Settings/Veerle/My Documents/code/bdarcus-cite'
              'proc-test-{}/processor-tests/machines'.format(TESTS_VERSION))



CATEGORY = ''
#CATEGORY = 'name_Parsed'
CATEGORY = 'disambiguate'
CATEGORY = 'sort_'
CATEGORY = 'textcase_'
CATEGORY = 'date_'
#CATEGORY = 'date_*Sort*'
#CATEGORY = 'locator_'
#CATEGORY = 'fullstyles_APA'
#CATEGORY = 'bugreports_AuthorYear'
#CATEGORY = 'locator_'
#CATEGORY = 'sort_'
#CATEGORY = 'bugreports_DemoPageFullCiteCruftOnSubsequent'

#CATEGORY = 'group_ComplexNesting'
#CATEGORY = 'sort_EtAlUseLast'

#CATEGORY = 'bugreports_NoEventInNestedMacroWithOldProcessor'
CATEGORY = 'condition_'
#CATEGORY = 'sort_'
CATEGORY = 'sort_AguStyle'
#CATEGORY = 'sort_AguStyleReverseGroups'
#CATEGORY = 'sort_AuthorDateWithYearSuffix'

CATEGORY = ''


# quotes
#CATEGORY = 'quotes_Punctuation'

# double dots
#CATEGORY = 'name_SubstituteInheritLabel'
#CATEGORY = 'bugreports_AllCapsLeakage'
#CATEGORY = 'punctuation_DelimiterWithStripPeriodsAndSubstitute2'
#CATEGORY = 'punctuation_SemicolonDelimiter'

# citations
#CATEGORY = 'bugreports_AutomaticallyDeleteItemsFails'
#CATEGORY = 'punctuation_DefaultYearSuffixDelimiter'
#CATEGORY = 'punctuation_SuppressPrefixPeriodForDelimiterSemicolon'

# position
#CATEGORY = 'bugreports_FourAndFour'
#CATEGORY = 'bugreports_MovePunctuationInsideQuotesForLocator'


class ProcessorTest(object):
    def __init__(self, filename):
        with open(filename, encoding='UTF-8') as f:
            self.json_data = json.load(f)

        csl_io = io.BytesIO(utf_8_encode(self.json_data['csl'])[0])
        self.style = CitationStylesStyle(csl_io)
        self.references = self.parse_references(self.json_data['input'])
        self.references_dict = {ref.key: ref for ref in self.references}
        self.bibliography = CitationStylesBibliography(self.style,
                                                       self.references_dict)
        self.expected = self.json_data['result'].splitlines()

    def parse_references(self, json_data):
        references = []
        for ref in json_data:
            ref_data = {}
            for key, value in ref.items():
                python_key = key.replace('-', '_')
                if python_key == 'id':
                    ref_key = value
                    continue
                if python_key == 'type':
                    ref_type = value
                    continue
                elif python_key in NAMES:
                    value = self.parse_names(value)
                elif python_key in DATES:
                    value = self.parse_date(value)
                elif python_key == 'shortTitle':
                    python_key = 'title_short'

                ref_data[python_key] = value
            references.append(Reference(ref_key, ref_type, **ref_data))
        return references

    def parse_names(self, json_data):
        names = []
        for name_data in json_data:
            name = Name(**name_data)
            names.append(name)
        return names

    def parse_date(self, json_data):
        def parse_single_date(json_date):
            date_data = {}
            try:
                for i, part in enumerate(('year', 'month', 'day')):
                    date_data[part] = json_date[i]
            except IndexError:
                pass
            return date_data

        dates = []
        for json_date in json_data['date-parts']:
            dates.append(parse_single_date(json_date))

        circa = json_data.get('circa', 0) != 0

        if len(dates) > 1:
            return DateRange(begin=Date(**dates[0]), end=Date(**dates[1]),
                             circa=circa)
        else:
            return Date(circa=circa, **dates[0])

    def execute(self):
        if self.json_data['citation_items']:
            citations = [self.parse_citation(item)
                         for item in self.json_data['citation_items']]
        elif self.json_data['citations']:
            citations = []
            for cit in self.json_data['citations']:
                cit = cit[0]
                citation_items = [self.parse_citation_item(cititem)
                                  for cititem in cit['citationItems']]
                citation = Citation(citation_items)
                citation.key = cit['citationID']
                citation.note_index = cit['properties']['noteIndex']
                citations.append(citation)
        elif self.json_data['bibentries']:
            citation_items = [self.parse_citation_item({'id': entry})
                              for entry in self.json_data['bibentries'][-1]]
            citations = [Citation(citation_items)]
        else:
            if self.json_data['mode'] == 'citation':
                self.references.sort(key=lambda e: e.key)
            citation_items = [self.parse_citation_item({'id': ref.key})
                              for ref in self.references]
            citations = [Citation(citation_items)]

        for citation in citations:
            self.bibliography.register(citation)

        if self.style.has_bibliography():
            self.bibliography.sort()

        results = []
        if self.json_data['mode'] == 'citation':
            if self.json_data['citations']:
                for i, citation in enumerate(citations):
                    if i == len(citations) - 1:
                        dots_or_other = '>>'
                    else:
                        dots_or_other = '..'
                    results.append('{}[{}] '.format(dots_or_other, i) +
                                   self.bibliography.cite(citation))
            else:
                for citation in citations:
                    results.append(self.bibliography.cite(citation))
        elif self.json_data['mode'] in ('bibliography', 'bibliography-nosort'):
            results.append(self.bibliography.bibliography())

        return results

    def parse_citation(self, citation_data):
        citation_items = []
        for item in citation_data:
            citation_item = self.parse_citation_item(item)
            citation_items.append(citation_item)

        return Citation(citation_items)

    def parse_citation_item(self, citation_item_data):
        options = {}
        for key, value in citation_item_data.items():
            python_key = key.replace('-', '_')
            if python_key == 'id':
                reference_key = value
                continue
            elif python_key == 'locator':
                try:
                    options['locator'] = Locator(citation_item_data['label'],
                                                 value)
                except KeyError:
                    # some tests don't specify the label
                    options['locator'] = Locator(None, value)
            elif python_key == 'label':
                pass
            else:
                options[python_key] = value

        return CitationItem(reference_key, **options)


if __name__ == '__main__':
    total = {}
    passed = {}
    max_tests = -1

    count = 0
    for filename in glob.glob(os.path.join(TESTS_PATH,
                                           '{}*.json'.format(CATEGORY))):
        category = os.path.basename(filename).split('_')[0]
        passed[category] = passed.get(category, 0)
        if count == max_tests:
            break

        try:
            t = ProcessorTest(filename)
            if (t.json_data['mode'] == 'bibliography-header' or
                t.json_data['bibsection']):
                continue
            total[category] = total.get(category, 0) + 1
            count += 1
            print('>>> Testing {}'.format(os.path.basename(filename)))
            print('EXP: ' + '\n     '.join(t.expected))

            results = t.execute()
            results = reduce(lambda x, y: x+y,
                             [item.split('\n') for item in results])
            results = [item.replace('&amp;', '&').replace('&', '&#38;')
                       for item in results]
            print('RES: ' + '\n     '.join(results))
            if results == t.expected:
                passed[category] += 1
                print('<<< SUCCESS\n')
            else:
                print('<<< FAILED\n')
            del t
        except Exception as e:
            print('Exception in', os.path.basename(filename))
            #traceback.print_exc(file=sys.stdout)
            #raise
            print(e)

    for category in sorted(total.keys()):
        print('{} passed {}/{}'.format(category, passed[category],
                                       total[category]))

    print('total: {}/{}'.format(sum(passed.values()), sum(total.values())))
