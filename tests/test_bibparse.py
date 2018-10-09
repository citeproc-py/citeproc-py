# coding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

import os

from io import StringIO
from unittest import TestCase

from citeproc.source.bibtex.bibparse import BibTeXParser, BibTeXDecodeError


TEST_BIB = os.path.join(os.path.dirname(__file__), 'test.bib')


class TestBibTeXParser(TestCase):
    def test_parse(self):
        file = StringIO(sample)
        bib = BibTeXParser(file)
        self.print_entries(bib)
        # TODO: perform useful checks

    def test_parse_file(self):
        test_bib = BibTeXParser(TEST_BIB, encoding='utf-8')
        self.print_entries(test_bib)

    def test_parse_file_bad_encoding(self):
        with self.assertRaises(BibTeXDecodeError):
            BibTeXParser(TEST_BIB)

    @staticmethod
    def print_entries(bib):
        for key, entry in bib.items():
            print(key)
            for name, value in entry.items():
                print('   {}: {}'.format(name, value))


# based on the sample BibTeX database by Xavier Décoret
# http://artis.imag.fr/~Xavier.Decoret/resources/xdkbibtex/bibtex_summary.html

sample = r"""
@Article(py03,
     author = {Xavier D\'ecoret},
     title  = "PyBiTex",
     year   = 2003
)

@Article{key03,
  title = "A {bunch {of} braces {in}} title"
}

@Article{key01a,
  author = "Simon {"}the {saint"} Templar",
}

@Article{key01b,
  title = "The history of @ sign"
}

Some {{comments} with unbalanced braces
....and a "commented" entry...

Book{landru21,
  author =	 {Landru, Henri D\'esir\'e},
  title =	 {A hundred recipes for you wife},
  publisher =	 {Culinary Expert Series},
  year =	 1921
}

..some other comments..before a valid entry...

@Book{steward03a,
  author =	 { Martha Steward },
  title =	 {Cooking behind bars},
  publisher =	 {Culinary Expert Series},
  year =	 2003
}

...and finally an entry commented by the use of the special @Comment entry type.

@Comment{steward03b,
  author =	 {Martha Steward},
  title =	 {Cooking behind bars},
  publisher =	 {Culinary Expert Series},
  year =	 2003
}

@Comment{
  @Book{steward03c,
    author =	 {Martha Steward},
    title =	 {Cooking behind bars},
    publisher =	 {Culinary Expert Series},
    year =	 2003
  }
}

@String(mar = "march")

@Book{sweig42,
  Author =	 { Stefan Sweig },
  title =	 { The impossible book },
  publisher =	 { Dead Poet Society},
  year =	 1942,
  month =        mar
}


@String {firstname = "Xavier"}
@String {lastname  = "Decoret"}
@String {email      = firstname # "." # lastname # "@imag.fr"}

@preamble{ "\newcommand{\noopsort}[1]{} "
        # "\newcommand{\printfirst}[2]{#1} "
        # "\newcommand{\singleletter}[1]{#1} "
        # "\newcommand{\switchargs}[2]{#2#1} " }

@INBOOK{inbook-minimal,
   author = "Donald E. Knuth",
   title = "Fundamental Algorithms",
   publisher = "Addison-Wesley",
   year = "{\noopsort{1973b}}1973",
   chapter = "1.2",
}
"""
