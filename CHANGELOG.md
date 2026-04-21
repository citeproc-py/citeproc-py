# v0.9.2 (Tue Apr 21 2026)

#### 🐛 Bug Fix

- setup: add citeproc-py-styles to tests [#189](https://github.com/citeproc-py/citeproc-py/pull/189) ([@tmorrell](https://github.com/tmorrell))

#### Authors: 1

- Tom Morrell ([@tmorrell](https://github.com/tmorrell))

---

# v0.9.1 (Mon Apr 20 2026)

#### 🐛 Bug Fix

- Add Dependabot configuration for GitHub Actions [#185](https://github.com/citeproc-py/citeproc-py/pull/185) ([@tmorrell](https://github.com/tmorrell))
- tests: drop python 3.9 [#179](https://github.com/citeproc-py/citeproc-py/pull/179) ([@tmorrell](https://github.com/tmorrell))
- Fix ordinal suffixes when style has embedded locale without ordinal terms [#184](https://github.com/citeproc-py/citeproc-py/pull/184) ([@Copilot](https://github.com/Copilot))

#### Authors: 2

- [@Copilot](https://github.com/Copilot)
- Tom Morrell ([@tmorrell](https://github.com/tmorrell))

---

# v0.9.0 (Mon Aug 25 2025)

#### 🚀 Enhancement

- Feature/flexible style loading [#180](https://github.com/citeproc-py/citeproc-py/pull/180) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 1

- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# v0.8.3 (Mon Aug 18 2025)

#### 🐛 Bug Fix

- setup: match license label with actual text [#175](https://github.com/citeproc-py/citeproc-py/pull/175) ([@tmorrell](https://github.com/tmorrell))
- Fix Non-existent Terms [#156](https://github.com/citeproc-py/citeproc-py/pull/156) ([@JVickery-TBS](https://github.com/JVickery-TBS))

#### 🏠 Internal

- Remove hardcoded option for auto to onlyPublishWithReleaseLabel [#178](https://github.com/citeproc-py/citeproc-py/pull/178) ([@yarikoptic](https://github.com/yarikoptic))
- release action: missing semicolon [#177](https://github.com/citeproc-py/citeproc-py/pull/177) ([@tmorrell](https://github.com/tmorrell))
- release action: missing quotes [#176](https://github.com/citeproc-py/citeproc-py/pull/176) ([@tmorrell](https://github.com/tmorrell))
- coveralls: try to reenable [#163](https://github.com/citeproc-py/citeproc-py/pull/163) ([@tmorrell](https://github.com/tmorrell))

#### 📝 Documentation

- Fix some formatting issues in README [#164](https://github.com/citeproc-py/citeproc-py/pull/164) ([@alexfikl](https://github.com/alexfikl))

#### Authors: 4

- Alex Fikl ([@alexfikl](https://github.com/alexfikl))
- Jesse Vickery ([@JVickery-TBS](https://github.com/JVickery-TBS))
- Tom Morrell ([@tmorrell](https://github.com/tmorrell))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# v0.8.2 (Wed Mar 12 2025)

#### 🏠 Internal

- Explicitly specify utf-8 encoding while reading top level .md files for description [#162](https://github.com/citeproc-py/citeproc-py/pull/162) ([@yarikoptic](https://github.com/yarikoptic))
- Instruct that long description is in markdown and not ReST [#160](https://github.com/citeproc-py/citeproc-py/pull/160) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 1

- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# v0.8.1 (Wed Mar 12 2025)

#### 🏠 Internal

- release: checkout with submodules [#159](https://github.com/citeproc-py/citeproc-py/pull/159) ([@yarikoptic](https://github.com/yarikoptic))

#### Authors: 1

- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---

# v0.8.0 (Wed Mar 12 2025)

#### 🚀 Enhancement

- release: use GitHUb App token for checkout and push [#158](https://github.com/citeproc-py/citeproc-py/pull/158) ([@tmorrell](https://github.com/tmorrell))

#### ⚠️ Pushed to `master`

- Rename CHANGES to CHANGELOG ([@yarikoptic](https://github.com/yarikoptic))

#### 🏠 Internal

- release: switch to using GitHub App to overcome branch protection [#157](https://github.com/citeproc-py/citeproc-py/pull/157) ([@tmorrell](https://github.com/tmorrell))
- Set up `auto` to automate releases [#153](https://github.com/citeproc-py/citeproc-py/pull/153) ([@jwodder](https://github.com/jwodder) [@yarikoptic](https://github.com/yarikoptic))

#### 📝 Documentation

- Convert CHANGES.rst, CONTRIBUTING.rst, and README.md to markdown [#154](https://github.com/citeproc-py/citeproc-py/pull/154) ([@tmorrell](https://github.com/tmorrell))

#### Authors: 3

- John T. Wodder II ([@jwodder](https://github.com/jwodder))
- Tom Morrell ([@tmorrell](https://github.com/tmorrell))
- Yaroslav Halchenko ([@yarikoptic](https://github.com/yarikoptic))

---


# Release 0.7.0 (2025-02-19)

Just to get a release out after long period.

#### Bug fixes

* Better handling of ordinals
* Fix locator conditions (resolves #142)
* Make family name optional
* Allow date parts to not be integers
* Support space macros
* Fix multiple capitals
* Fix parsing BibTex integer values

#### Other changes:

* Removed support for Python 3.6, 3.7, 3.8 and added for 3.10 - 3.13
* Switch versioning to versioneer


# Release 0.6.0 (2021-05-27)

#### Bug fixes

* Various issues on Windows: testing, explicit utf-8 encoding
* Strings with unescaped \ declared r"aw"

#### Other changes:

* Removed support for Python 2.7, 3.5 and added for 3.9
* Travis CI is removed in favor of GitHub actions testing across
  all 3 major OSes (MacOS, Windows, GNU/Linux Ubuntu)
* CSL test-suite progressed from 5779a8c to c3db429


# Release 0.5.1 (2020-03-06)

#### Bug fixed:

* avoid rnc2rng 2.6.2 which breaks installation of citeproc-py

# Release 0.5.0 (2020-02-09)

#### Enhancements:

* handle commas and ampersands in a functional style
* Number: handle commas and ampersands
* added symbol for textquotesingle
* specify fallback locales for fr-CA and es-CL
* improved page number and ranges parsing

#### Bug fixed:

* don't fail on empty page ranges (#90) (bbm)
* detect end of file while parsing incorrect bib (#59) (John Vandenberg)

#### Other changes:

* Removed 3.2-3.4 and added 3.7, 3.8 to supported Pythons
* Refactored locales handling

# Release 0.4.0 (2017-06-23)

#### New features:

* allow specifying the encoding of a BibTeX database file (#20 and #25)
* BibTeX 'month' field: support integers and "<month> <day>" values
* BibTeX 'pages' field: support "10", "10+", "10-12" and "10--12" formats
* BibTeX entry types: map the non-standard 'thesis' and 'report' entries
* update the CSL schema to version 1.0.1 (#5)
* update the CSL locales to commit 49bf3fc0

#### Bug fixed:

* avoid crash when there is nothing to affix (David Lesieur)
* fix BibTeX month to CSL month mapping (#24)
* strip leading/trailing whitespace from BibTeX values (#37)

# Release 0.3.0 (2014-11-07)

#### Major improvements to the BibTeX parser:

* split names into parts and assign them to the equivalent CSL name parts
* fixed handling of accent macros and escaped characters
* more compatible (La)TeX macro handling in general (but still basic)
* handle standard Computer Modern ligatures such as --, ---, and <<
* added unit tests for the BibTeX and LaTeX parsers

#### Other changes:

* disable RelaxNG validation of CSL styles by default (API change)

# Release 0.2.0 (2014-10-25)

* bad cite callback function can determine how a bad cite is displayed (hetsch)
* added option to disable RelaxNG validation (Jasper Op de Coul)
* distutils was replaced with setuptools (Joshua Carp)
* bug fixes (Yaroslav Halchenko, David Lesieur)
* CitationStylesBibliography.bibliography() now returns the list of entries
