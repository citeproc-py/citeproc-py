# citeproc-py

[![PyPI - Version](https://img.shields.io/pypi/v/citeproc-py)](https://pypi.org/project/citeproc-py/)
[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/citeproc-py/citeproc-py/test.yml)](https://github.com/citeproc-py/citeproc-py/actions?query=branch%3Amaster+workflow%3ATest)
[![Coveralls](https://img.shields.io/coverallsCoverage/github/citeproc-py/citeproc-py)](https://coveralls.io/github/citeproc-py/citeproc-py)


citeproc-py is a [CSL](https://citationstyles.org/) processor for Python. It aims to implement the
[CSL 1.0.2 specification](https://docs.citationstyles.org/en/v1.0.2/specification.html).
citeproc-py can output styled citations and
bibliographies in a number of different output formats. Currently
supported are plain text, reStructuredText and HTML. Other formats can
be added easily.

citeproc-py uses [semantic versioning](https://semver.org/). Currently, its major version
number is still at 0, meaning the API is not yet stable. However, you
should not expect to see any major API changes soon.

## Requirements

citeproc-py supports Python 3.9 and up. It depends on [lxml](https://lxml.de/) for parsing and
navigating the CSL style and locale files.

# Installation

The recommended way of installing citeproc-py is by using
[pip](https://pip.pypa.io/en/latest/):
```bash
   pip install citeproc-py
```

If `lxml` isn't installed, `pip` will try to install it for you.

If you insist, you can manually install citeproc-py from distribution packages
hosted at [PyPI](https://pypi.python.org/pypi/citeproc-py/). Please ignore the release archives offered by GitHub.

## Getting Started

To get started with citeproc-py, take a look at the examples under
`examples/`. Two examples are provided, one parsing references from a
JSON representation of references as supported by citeproc-js, another
parsing the references from a BibTeX file. Both show and explain how to
cite references and render the bibliography.

## CSL Compatibility

Currently, citeproc-py passes about 60% of the tests in the
[citeproc-test suite](https://github.com/citation-style-language/test-suite).
A non-exhaustive list of functionality that is missing includes:

-  disambiguation/year-suffix
-  et-al-subsequent-min/et-al-subsequent-use-first
-  collapsing
-  punctuation-in-quote
-  display

Also, some [citeproc-js](https://github.com/juris-m/citeproc-js)
functionality that is not part of the CSL spec is not (yet) supported:

-  raw dates
-  static-ordering
-  literal names

## Contributing

citeproc-py is 100% volunteer maintained, and new contributions are always welcome.
If you would like to contribute, please follow the guidelines in the
[CONTRIBUTING.md](https://github.com/citeproc-py/citeproc-py/blob/master/CONTRIBUTING.md) file.

## Local Install and Running the Tests

First clone the `citeproc-py` repository and its submodules with
```bash
git clone --recurse-submodules https://github.com/citeproc-py/citeproc-py
```
and install `citeproc-py` with
```bash
python -m pip install --editable .
```

If installed correctly, you should be able to run the tests. For example, you
can run the full `citeproc` test suite using
```bash
python tests/citeproc-test.py
```
and the `citeproc-py` specific test suite using
```bash
python -m unittest discover --buffer --verbose tests
# or
python -m pytest --capture=no --verbose tests
```

You can check out `citeproc-test.py --help` to see more usage information for
this script. The first time you run the script it will clone the [citeproc-test
suite](https://github.com/citation-style-language/test-suite) repository into
the `tests` directory and checkout the last tested version. By default failed
tests are automatically added into the `tests/failing_tests.txt` file and are not
shown when running the test suite again.

`citeproc-py` uses `ruff` for linting. You can run it directly using `ruff check`.
Any test failures or linting errors will show up on the CI and will need to be
fixed before a Pull Request can be merged.
