

import glob
import io
import json
import os
import sys
import traceback

from codecs import utf_8_encode
from functools import reduce
from optparse import OptionParser

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc.source import Citation, CitationItem, Locator
from citeproc.source.json import CiteProcJSON


TESTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                          os.path.pardir, os.path.pardir,
                                          'citeproc-test', 'processor-tests',
                                          'machines'))


class ProcessorTest(object):
    def __init__(self, filename):
        with open(filename, encoding='UTF-8') as f:
            self.json_data = json.load(f)

        csl_io = io.BytesIO(utf_8_encode(self.json_data['csl'])[0])
        self.style = CitationStylesStyle(csl_io)
        self.references = [item['id'] for item in self.json_data['input']]
        self.references_dict = CiteProcJSON(self.json_data['input'])
        self.bibliography = CitationStylesBibliography(self.style,
                                                       self.references_dict)
        self.expected = self.json_data['result'].splitlines()

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
                self.references.sort()
            citation_items = [self.parse_citation_item({'id': ref})
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


def main():
    usage = ('usage: %prog [options] glob_pattern\n\n'
             'glob_pattern limits the tests that are executed, for example:\n'
             '  %prog *Sort*\n'
             'runs only test fixtures that have "Sort" in the filename')
    parser = OptionParser(usage)
    parser.add_option('-m', '--max', dest='max', default=-1,
                      help='run maximally MAX tests', metavar='MAX')
    parser.add_option('-r', '--raise', dest='catch_exceptions', default=True,
                      action='store_false',
                      help='exceptions are not caught (aborts program)')
    parser.add_option('-f', '--file', dest='file', default=None,
                      help='write output to FILE', metavar='FILE')
    (options, args) = parser.parse_args()

    try:
        destination = open(options.file, 'w', encoding='utf-8')
        sys.stderr = destination
    except TypeError:
        destination = sys.stdout

    try:
        glob_pattern = args[0]
        filter_tests = False
    except IndexError:
        glob_pattern = '*'
        filter_tests = True

    total = {}
    passed = {}
    max_tests = int(options.max)

    count = 0
    for filename in glob.glob(os.path.join(TESTS_PATH,
                                           '{}.json'.format(glob_pattern))):
        category = os.path.basename(filename).split('_')[0]
        passed[category] = passed.get(category, 0)
        if count == max_tests:
            break

        try:
            t = ProcessorTest(filename)
            if filter_tests and (t.json_data['mode'] == 'bibliography-header' or
                                 t.json_data['bibsection']):
                continue
            total[category] = total.get(category, 0) + 1
            count += 1
            print('>>> Testing {}'.format(os.path.basename(filename)),
                  file=destination)
            print('EXP: ' + '\n     '.join(t.expected), file=destination)

            results = t.execute()
            results = reduce(lambda x, y: x+y,
                             [item.split('\n') for item in results])
            results = [item.replace('&amp;', '&#38;')
                       for item in results]
            print('RES: ' + '\n     '.join(results), file=destination)
            if results == t.expected:
                passed[category] += 1
                print('<<< SUCCESS\n', file=destination)
            else:
                print('<<< FAILED\n', file=destination)
            del t
        except Exception as e:
            print('Exception in', os.path.basename(filename), file=destination)
            if options.catch_exceptions:
                traceback.print_exc(file=destination)
            else:
                raise

    for category in sorted(total.keys()):
        print('{} passed {}/{}'.format(category, passed[category],
                                       total[category]), file=destination)

    print('total: {}/{}'.format(sum(passed.values()), sum(total.values())),
          file=destination)


if __name__ == '__main__':
    main()
