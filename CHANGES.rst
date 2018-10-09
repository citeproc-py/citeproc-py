Changelog
---------

Release 0.4.0 (2017-06-23)
~~~~~~~~~~~~~~~~~~~~~~~~~~

New features:

* allow specifying the encoding of a BibTeX database file (#20 and #25)
* BibTeX 'month' field: support integers and "<month> <day>" values
* BibTeX 'pages' field: support "10", "10+", "10-12" and "10--12" formats
* BibTeX entry types: map the non-standard 'thesis' and 'report' entries
* update the CSL schema to version 1.0.1 (#5)
* update the CSL locales to commit 49bf3fc0

Bug fixed:

* avoid crash when there is nothing to affix (David Lesieur)
* fix BibTeX month to CSL month mapping (#24)
* strip leading/trailing whitespace from BibTeX values (#37)

Release 0.3.0 (2014-11-07)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Major improvements to the BibTeX parser:

* split names into parts and assign them to the equivalent CSL name parts
* fixed handling of accent macros and escaped characters
* more compatible (La)TeX macro handling in general (but still basic)
* handle standard Computer Modern ligatures such as --, ---, and <<
* added unit tests for the BibTeX and LaTeX parsers

Other changes:

* disable RelaxNG validation of CSL styles by default (API change)

Release 0.2.0 (2014-10-25)
~~~~~~~~~~~~~~~~~~~~~~~~~~

* bad cite callback function can determine how a bad cite is displayed (hetsch)
* added option to disable RelaxNG validation (Jasper Op de Coul)
* distutils was replaced with setuptools (Joshua Carp)
* bug fixes (Yaroslav Halchenko, David Lesieur)
* CitationStylesBibliography.bibliography() now returns the list of entries
