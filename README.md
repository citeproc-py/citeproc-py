# citeproc-py

![PyPI - Version](https://img.shields.io/pypi/v/citeproc-py)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/citeproc-py/citeproc-py/test.yml)
![Coveralls](https://img.shields.io/coverallsCoverage/github/citeproc-py/citeproc-py)


citeproc-py is a [`CSL`](https://citationstyles.org/) processor for Python. It aims to implement the
[CSL 1.0.1 specification](https://docs.citationstyles.org/en/1.0.1/specification.html). 
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

   pip install citeproc-py

If lxml isn't installed, pip will try to install it for you.

If you insist, you can manually install citeproc-py from distribution packages
hosted at [PyPI](https://pypi.python.org/pypi/citeproc-py/). Please ignore the release archives offered by GitHub.

## Getting Started

To get started with citeproc-py, take a look at the examples under
`examples/`. Two examples are provided, one parsing references from a
JSON representation of references as supported by citeproc-js, another
parsing the references from a BibTeX file. Both show and explain how to
cite references and render the bibliography.

## CSL Compatibility

Currently, citeproc-py passes almost 60% of the (relevant) tests in the
[citeproc-test suite](https://github.com/citation-style-language/test-suite). 
However, it is more than 60% complete, as
citeproc-py doesn't take care of double spaces and repeated punctuation
marks yet, making a good deal of the tests fail. In addition, the
following features have not yet been implemented (there are probably
some I forgot though):

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

First clone the `citeproc-py` repository and install the submodules with 

`git submodule update --init` 

Then install with 

`pip install -e .`

Then move to the `tests` directory and run 

`python citeproc-test.py`

Run 

`citeproc-test.py --help` 

to see its usage information. The first time
you run the script it will clone the 
[citeproc-test suite](https://github.com/citation-style-language/test-suite) repository into the
`tests` directory and checkout the last tested version. By default failed tests are
automatically added into the `failing_tests.txt` file and aren't shown when
running the test suite again.

If you want git to fully ignore the submodule, you can type 

`git update-index --assume-unchanged citeproc/data/schema`
