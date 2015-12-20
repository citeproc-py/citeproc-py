
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

FAILING_TESTS_FILE = 'failing_tests.txt'


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
    """Parses atest fixture and provides a method for processing the tests
    defined in it."""
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
                if 'citationID' in cit:
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
    """Read the known failed tests from a file and update the file with the
    results from a new test run."""
    def __init__(self, filename):
        self.filename = filename
        with open(filename, 'r') as file:
            self.lines = file.readlines()
        self.now_failing = {}

    def mark_failure(self, test_name, reason=None):
        self.now_failing[test_name] = reason

    def update_file(self):
        was_failing = set()
        new_failing_tests = []
        new_fixed_tests = []
        with open(self.filename, 'w') as file:
            for line in self.lines:
                test_name, comment = (line.split('#') if '#' in line
                                      else (line, None))
                test_name = test_name.strip()
                if test_name and test_name not in self.now_failing:
                    new_fixed_tests.append(test_name)
                    continue
                was_failing.add(test_name)
                file.write(line)
            for test_name in sorted(self.now_failing.keys()):
                if test_name not in was_failing:
                    reason = self.now_failing[test_name]
                    line = ('{:<66} # {}'.format(test_name, reason) if reason
                            else test_name)
                    print(line, file=file)
                    new_failing_tests.append(test_name)
        return new_failing_tests, new_fixed_tests


def execute_hg_command(args, echo=False):
    """Execute a mercurial command, exiting this script when it returns a
    non-zero error code."""
    command = ['hg'] + args
    if echo:
        print(' '.join(command))
    process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    if process.returncode:
        print('Calling Mercurial failed. Make sure Mercurial (hg) is \n'
              'installed. Aborting.')
        sys.exit(1)
    return out, err


def clone_citeproc_test():
    """Clone the citeproc-test repository if it is not present. Otherwise, check
    whether the correct commit is checked out."""
    if not os.path.exists(CITEPROC_TEST_PATH):
        hg_clone = ['clone', '--rev', CITEPROC_TEST_COMMIT,
                    CITEPROC_TEST_REPOSITORY, CITEPROC_TEST_PATH]
        print('Cloning the citeproc-test repository...')
        execute_hg_command(hg_clone, echo=True)
    else:
        hg_id = ['-R', CITEPROC_TEST_PATH, 'id', '--id']
        commit_id, _ = execute_hg_command(hg_id)
        if commit_id.strip() != CITEPROC_TEST_COMMIT.encode('ascii'):
            print('The checked-out commit of citeproc-test does not match \n'
                  'the one recorded in this test script. Aborting.')
            sys.exit(1)
        hg_pull = ['-R', CITEPROC_TEST_PATH, 'pull']
        execute_hg_command(hg_pull)
    hg_tip_id = ['-R', CITEPROC_TEST_PATH, 'id', '--id', '--rev', 'tip']
    tip_commit_id, _ = execute_hg_command(hg_tip_id)
    has_updates = tip_commit_id.strip() != CITEPROC_TEST_COMMIT.encode('ascii')
    return has_updates


RED = '\033[91m'
GREEN = '\033[92m'
BOLD = '\033[1m'
END = '\033[0m'


if __name__ == '__main__':
    usage = ('usage: %prog [options] glob_pattern\n\n'
             'glob_pattern limits the tests that are executed, for example:\n'
             '  %prog *Sort*\n'
             'runs only test fixtures that have "Sort" in the filename')
    parser = OptionParser(usage)
    parser.add_option('-m', '--max', dest='max', default=-1,
                      help='run up to MAX tests', metavar='MAX')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
                      default=False, help='print results for each test')
    parser.add_option('-r', '--raise', dest='catch_exceptions', default=True,
                      action='store_false',
                      help='do not catch exceptions (aborts program)')
    parser.add_option('-s', '--summary', dest='summary', action='store_true',
                      default=False, help='print a summary of the test results')
    parser.add_option('-f', '--file', dest='file', default=None,
                      help='write output to FILE', metavar='FILE')
    (options, args) = parser.parse_args()

    max_tests = int(options.max)
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

    test_repo_has_updates = clone_citeproc_test()

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
                                            FAILING_TESTS_FILE))
    count = 0
    test_files = os.path.join(TESTS_PATH, '{}.txt'.format(glob_pattern))
    for filename in sorted(glob.glob(test_files)):
        test_name, _ = os.path.basename(filename).split('.txt')
        category, _ = os.path.basename(filename).split('_')
        passed_count.setdefault(category, 0)
        if count == max_tests:
            break

        reason = None
        try:
            if test_name not in IGNORED_RESULS:
                total_count[category] = total_count.get(category, 0) + 1
                count += 1
            t = ProcessorTest(filename)
            if filter_tests and (t.data['mode'] == 'bibliography-header' or
                                 t.data['bibsection']):
                continue
            if options.verbose:
                out('>>> Testing {}'.format(os.path.basename(filename)))
                out('EXP: ' + '\n     '.join(t.expected))

            results = t.execute()
            results = reduce(lambda x, y: x+y,
                             [item.split('\n') for item in results])
            results = [item.replace('&amp;', '&#38;')
                       for item in results]
            if options.verbose:
                out('RES: ' + '\n     '.join(results))
            if results == t.expected:
                if test_name not in IGNORED_RESULS:
                    passed_count[category] += 1
                if options.verbose:
                    out('<<< SUCCESS\n')
                continue
            else:
                if options.verbose:
                    out('<<< FAILED\n')
            del t
        except Exception as e:
            reason = 'uncaught exception'
            if options.verbose:
                out('Exception in', os.path.basename(filename))
            if options.catch_exceptions:
                if options.verbose:
                    traceback.print_exc()
            else:
                raise
        if test_name not in IGNORED_RESULS:
            failed_tests.mark_failure(test_name, reason)

    success = True
    if sum(total_count.values()) == 0:
        print('<no tests found>: check README.md file for instructions')
    else:
        def print_result(name, passed, total):
            out(' {:<13} {:>3} / {:>3} ({:>4.0%})'.format(name, passed, total,
                                                          passed / total))
        new_failing, new_fixed = failed_tests.update_file()
        success = not (new_failing or new_fixed)

        if new_failing:
            out(BOLD + 'New failing tests:' + END)
            for test_name in new_failing:
                out(' ' + RED + test_name + END)
        if new_failing and new_fixed:
            out()
        else:
            out('All is well.')
        if new_fixed:
            out(BOLD + 'Fixed tests:' + END)
            for test_name in new_fixed:
                out(' ' + GREEN + test_name + END)
            out()
            out('You need to fix the newly failing tests and may commit the \n'
                'removal of the fixed tests from {}'.format(FAILING_TESTS_FILE))

        if test_repo_has_updates:
            out()
            out(BOLD + 'The citeproc-test repository has updates! Consider '
                       'updating the test script.' + END)

        if options.summary:
            out()
            out(BOLD + 'Summary:' + END)
            for category in sorted(total_count.keys()):
                print_result(category, passed_count[category],
                             total_count[category])
            out()
            print_result('total', sum(passed_count.values()),
                         sum(total_count.values()))
    try:
        destination.close()
    except AttributeError:
        pass
    sys.exit(0 if success else 1)
