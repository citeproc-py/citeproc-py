citeproc-py
===========

citeproc-py is a [CSL][csl] processor for Python. It aims to implement the 
[CSL 1.0.1 specification][csl_spec].

citeproc-py has been developed for Python 3 but also runs on Python 2.6+. It
depends on [lxml][lxml] for parsing and navigating the CSL style and locale
files.

[csl]: http://citationstyles.org/
[csl_spec]: http://citationstyles.org/documentation/
[lxml]: http://lxml.de/


Getting Started
---------------

To get started with citeproc-py, take a look at the examples under `examples/`.
Two examples are provided, one parsing references from a JSON representation of
references as supported by citeproc-js, another parsing the references from
a BibTeX file. Both show and explain how to cite references and render the
bibliography.


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
* collapsing
* punctuation-in-quote
* display

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
