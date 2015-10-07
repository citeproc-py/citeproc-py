
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *


import glob
import io
import os
import sys
import traceback

from codecs import utf_8_encode
from functools import reduce
from optparse import OptionParser
from subprocess import Popen, PIPE

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc.source import Citation, CitationItem, Locator
from citeproc.source.json import CiteProcJSON


CITEPROC_TEST_REPOSITORY = 'https://bitbucket.org/bdarcus/citeproc-test'
CITEPROC_TEST_COMMIT = 'b15130259c4c'

CITEPROC_TEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                     'citeproc-test'))
TEST_PARSER_PATH = os.path.join(CITEPROC_TEST_PATH, 'processor.py')
TESTS_PATH = os.path.join(CITEPROC_TEST_PATH, 'processor-tests', 'humans')

# The results of the following tests are ignored, since they don't test CSL
# features, but citeproc-js specific features

IGNORED_RESULS = {
    'date_Accessed': 'raw date',
    'date_LoneJapaneseMonth': 'raw date',
    'date_LopsidedDataYearSuffixCollapse': 'raw date',
    'date_RawParseSimpleDate': 'raw date',
    'date_RawSeasonRange1': 'raw date',
    'date_RawSeasonRange2': 'raw date',
    'date_RawSeasonRange3': 'raw date',
    'date_String': 'raw date',
}


class ProcessorTest(object):
    bib_prefix = '<div class="csl-bib-body">'
    bib_suffix = '</div>'
    item_prefix = '  <div class="csl-entry">'
    item_suffix = '</div>'

    def __init__(self, filename):
        self.csl_test = CslTest({}, None, (filename, ),
                                os.path.basename(filename))
        self.csl_test.parse()
        csl_io = io.BytesIO(utf_8_encode(self.data['csl'])[0])
        self.style = CitationStylesStyle(csl_io)
        self._fix_input(self.data['input'])
        self.references = [item['id'] for item in self.data['input']]
        self.references_dict = CiteProcJSON(self.data['input'])
        self.bibliography = CitationStylesBibliography(self.style,
                                                       self.references_dict)
        self.expected = self.data['result'].splitlines()

    @property
    def data(self):
        return self.csl_test.data

    @staticmethod
    def _fix_input(input_data):
        for i, ref in enumerate(input_data):
            if 'id' not in ref:
                ref['id'] = i
            if 'type' not in ref:
                ref['type'] = 'book'

    def execute(self):
        if self.data['citation_items']:
            citations = [self.parse_citation(item)
                         for item in self.data['citation_items']]
        elif self.data['citations']:
            citations = []
            for cit in self.data['citations']:
                cit = cit[0]
                citation_items = [self.parse_citation_item(cititem)
                                  for cititem in cit['citationItems']]
                citation = Citation(citation_items)
                citation.key = cit['citationID']
                citation.note_index = cit['properties']['noteIndex']
                citations.append(citation)
        elif self.data['bibentries']:
            citation_items = [self.parse_citation_item({'id': entry})
                              for entry in self.data['bibentries'][-1]]
            citations = [Citation(citation_items)]
        else:
            citation_items = [self.parse_citation_item({'id': ref})
                              for ref in self.references]
            citations = [Citation(citation_items)]

        for citation in citations:
            self.bibliography.register(citation)

        if self.style.has_bibliography():
            self.bibliography.sort()

        results = []
        do_nothing = lambda x: None     # callback passed to cite()
        if self.data['mode'] == 'citation':
            if self.data['citations']:
                for i, citation in enumerate(citations):
                    if i == len(citations) - 1:
                        dots_or_other = '>>'
                    else:
                        dots_or_other = '..'
                    results.append('{}[{}] '.format(dots_or_other, i) +
                                   self.bibliography.cite(citation, do_nothing))
            else:
                for citation in citations:
                    results.append(self.bibliography.cite(citation, do_nothing))
        elif self.data['mode'] in ('bibliography', 'bibliography-nosort'):
            results.append(self.bib_prefix)
            for entry in self.bibliography.bibliography():
                text = self.item_prefix + str(entry) + self.item_suffix
                results.append(text)
            results.append(self.bib_suffix)

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
                reference_key = str(value)
                continue
            elif python_key == 'locator':
                try:
                    options['locator'] = Locator(citation_item_data['label'],
                                                 value)
                except KeyError:
                    # some tests don't specify the label
                    options['locator'] = Locator('page', value)
            elif python_key == 'label':
                pass
            else:
                options[python_key] = value

        return CitationItem(reference_key, **options)


class FailedTests(object):
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as file:
            self.lines = file.readlines()
        self.now_failing = []

    def mark_failure(self, test_name):
        self.now_failing.append(test_name)

    def update_file(self):
        was_failing = set()
        with open(self.filename, 'w') as file:
            for line in self.lines:
                test_name, comment = (line.split('#') if '#' in line
                                      else (line, None))
                test_name = test_name.strip()
                if test_name and test_name not in self.now_failing:
                    continue
                was_failing.add(test_name)
                file.write(line)
            for test_name in sorted(self.now_failing):
                if test_name not in was_failing:
                    print(test_name, file=file)


def execute_hg_command(args, echo=False):
    command = ['hg'] + args
    if echo:
        print(' '.join(command))
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    if process.returncode:
        print('Calling Mercurial failed. Make sure Mercurial (hg) '
              'is installed. Aborting.')
        sys.exit(1)
    return out, err


def clone_citeproc_test():
    if not os.path.exists(CITEPROC_TEST_PATH):
        hg_clone = ['clone', '--rev', CITEPROC_TEST_COMMIT,
                    CITEPROC_TEST_REPOSITORY, CITEPROC_TEST_PATH]
        print('Cloning the citeproc-test repository...')
        execute_hg_command(hg_clone, echo=True)
    else:
        hg_id = ['-R', CITEPROC_TEST_PATH, 'id', '--id']
        out, err = execute_hg_command(hg_id)
        if out.strip() != CITEPROC_TEST_COMMIT.encode('ascii'):
            print('The checked-out commit of citeproc-test does not match '
                  'the one recorded in this test script. Aborting.')
            sys.exit(1)


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
        destination = open(options.file, 'wt', encoding='utf-8')
        class UnicodeWriter(object):
            def write(self, s):
                destination.write(str(s))
        sys.stderr = UnicodeWriter()
    except TypeError:
        destination = sys.stdout
    def out(*args):
        if not args:
            destination.write('\n')
        else:
            print(*args, file=destination)

    try:
        glob_pattern = args[0]
        filter_tests = False
    except IndexError:
        glob_pattern = '*'
        filter_tests = True

    clone_citeproc_test()

    # import the text fixture parser included with citeproc-test
    try:  # Python 3.3+
        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader('processor', TEST_PARSER_PATH)
        processor = loader.load_module()
    except ImportError:  # older Python versions
        from imp import load_source
        processor = load_source('processor', TEST_PARSER_PATH)
    from processor import CslTest
    global CslTest

    total_count = {}
    passed_count = {}
    failed_tests = FailedTests(os.path.join(os.path.dirname(__file__),
                                            'failing_tests.txt'))
    max_tests = int(options.max)

    count = 0
    test_files = os.path.join(TESTS_PATH, '{}.txt'.format(glob_pattern))
    for filename in sorted(glob.glob(test_files)):
        test_name, _ = os.path.basename(filename).split('.txt')
        category, _ = os.path.basename(filename).split('_')
        passed_count.setdefault(category, 0)
        if count == max_tests:
            break

        try:
            if test_name not in IGNORED_RESULS:
                total_count[category] = total_count.get(category, 0) + 1
                count += 1
            t = ProcessorTest(filename)
            if filter_tests and (t.data['mode'] == 'bibliography-header' or
                                 t.data['bibsection']):
                continue
            out('>>> Testing {}'.format(os.path.basename(filename)))
            out('EXP: ' + '\n     '.join(t.expected))

            results = t.execute()
            results = reduce(lambda x, y: x+y,
                             [item.split('\n') for item in results])
            results = [item.replace('&amp;', '&#38;')
                       for item in results]
            out('RES: ' + '\n     '.join(results))
            if results == t.expected:
                if test_name not in IGNORED_RESULS:
                    passed_count[category] += 1
                out('<<< SUCCESS\n')
                continue
            else:
                out('<<< FAILED\n')
            del t
        except Exception as e:
            out('Exception in', os.path.basename(filename))
            if options.catch_exceptions:
                traceback.print_exc()
            else:
                raise
        if test_name not in IGNORED_RESULS:
            failed_tests.mark_failure(test_name)

    if sum(total_count.values()) == 0:
        print('<no tests found>: check README.md file for instructions')
    else:
        def print_result(name, passed, total):
            out(' {:<13} {:>3} / {:>3} ({:>4.0%})'.format(name, passed, total,
                                                          passed / total))
        failed_tests.update_file()
        out('Failed tests:')
        for test_name in failed_tests.now_failing:
            out(' ' + test_name)

        out()
        out('Summary:')
        for category in sorted(total_count.keys()):
            print_result(category, passed_count[category], total_count[category])
        out()
        print_result('total', sum(passed_count.values()), sum(total_count.values()))
    try:
        destination.close()
    except AttributeError:
        pass


if __name__ == '__main__':
    main()
