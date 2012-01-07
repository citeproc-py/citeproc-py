citeproc-py
===========

citeproc-py is a CSL processor written in Python. It aims to implement CSL 1.0,
but already supports some CSL 1.0.1 features.

It has been developed using Python 3 and currently doesn't run under Python 2.x.
It shouldn't be too hard to get it to work in Python 2 though (3to2?). In
addition, citeproc-py depends on [lxml](http://lxml.de/) for parsing and
navigating the CSL styles and locale files.

citeproc-py has basic, incomplete support for loading reference data from a
BibTeX file.

CSL Compatibility
-----------------

Currently, citeproc-py passes almost 60% of the (relevant) tests in the
[citeproc-test suite](https://bitbucket.org/bdarcus/citeproc-test). However, it
is more than 60% complete, as citeproc-py doesn't take care of double spaces and
repeated punctuation marks yet, making a good deal of the tests fail. In
addition, the following features have not yet been implemented (there are
probably some I forgot though):

* disambiguation/year-suffix
* et-al-subsequent-min/et-al-subsequent-use-first
* position
* collapsing
* punctuation-in-quote
* page-range-format
* display
* text-case (incomplete)
* seasons

Also, some [citeproc-js](http://bitbucket.org/fbennett/citeproc-js/wiki/Home)
functionality that is not part of the CSL spec is not (yet) supported:

* raw dates
* static-ordering
* literal names


Running the Tests
-----------------

First clone the
[citeproc-test suite](https://bitbucket.org/bdarcus/citeproc-test) so that it
sits next to the citeproc-py directory. Then run the `processor.py` script to
generate the test fixtures (using Python 2.x). After that, you can run
`citeproc-test.py` (in the `tests` directory). Run `citeproc-test.py --help` to
see its usage information.


Brecht Machiels
