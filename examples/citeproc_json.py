#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

# We'll use json.loads for parsing the JSON data.
import json

# Import the citeproc-py classes we'll use below.
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem
from citeproc import formatter
from citeproc.source.json import CiteProcJSON


# The following JSON data describes 5 references picked from the CSL test suite.

json_input = """
[
    {
        "id": "ITEM-1",
        "issued": {
            "date-parts": [[1987,  8,  3],
                           [2003, 10, 23]]
        },
        "title": "Ignore me",
        "type": "book"
    },
    {
      "id" : "ITEM-2",
      "page" : "1-7",
      "type" : "article-journal",
      "issued" : {
        "date-parts": [[2006]]
      }
    },
    {
        "author": [
            {
                "family": "Doe",
                "given": "John"
            }
        ],
        "id": "ITEM-3",
        "issued": {
            "date-parts": [["1965", "6", "1"]]
        },
        "title": "His Anonymous Life",
        "type": "book"
    },
    {
        "author": [
            {
                "family": "Grignon",
                "given": "Cyril"
            },
                        {
                "family": "Sentenac",
                "given": "Corey"
            }
        ],
        "id": "ITEM-4",
        "issued": {
            "date-parts": [[2000]]
       },
        "type": "book"
    },
    {
        "id": "ITEM-5",
        "title":"Boundaries of Dissent: Protest and State Power in the Media Age",
        "author": [
                {
                        "family": "D'Arcus",
                        "given": "Bruce",
                        "static-ordering": false
                }
        ],
        "publisher": "Routledge",
        "publisher-place": "New York",
        "issued": {
            "date-parts":[[2006]]
        },
        "type": "book",
        "URL": "http://www.test01.com"
    }
]
"""


# Parse the JSON input using json.loads()
# (parsing from a file object can be done with json.load)

json_data = json.loads(json_input)

# Process the JSON data to generate a citeproc-py BibliographySource.

bib_source = CiteProcJSON(json_data)
##for key, entry in bib_source.items():
##    print(key)
##    for name, value in entry.items():
##        print('   {}: {}'.format(name, value))

# load a CSL style (from the current directory)

bib_style = CitationStylesStyle('harvard1', validate=False)

# Create the citeproc-py bibliography, passing it the:
# * CitationStylesStyle,
# * BibliographySource (CiteProcJSON in this case), and
# * a formatter (plain, html, or you can write a custom formatter)

bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.html)


# Processing citations in a document needs to be done in two passes as for some
# CSL styles, a citation can depend on the order of citations in the
# bibliography and thus on citations following the current one.
# For this reason, we first need to register all citations with the
# CitationStylesBibliography.

citation1 = Citation([CitationItem('ITEM-3')])
citation2 = Citation([CitationItem('ITEM-1'), CitationItem('ITEM-2')])
citation3 = Citation([CitationItem('ITEM-4')])
citation4 = Citation([CitationItem('ITEM-5')])
citation5 = Citation([CitationItem('MISSING')])

bibliography.register(citation1)
bibliography.register(citation2)
bibliography.register(citation3)
bibliography.register(citation4)
bibliography.register(citation5)


# In the second pass, CitationStylesBibliography can generate citations.
# CitationStylesBibliography.cite() requires a callback function to be passed
# along to be called in case a CitationItem's key is not present in the
# bibliography.

def warn(citation_item):
    print("WARNING: Reference with key '{}' not found in the bibliography."
          .format(citation_item.key))

print('Citations')
print('---------')

print(bibliography.cite(citation1, warn))
print(bibliography.cite(citation2, warn))
print(bibliography.cite(citation3, warn))
print(bibliography.cite(citation4, warn))
print(bibliography.cite(citation5, warn))


# And finally, the bibliography can be rendered.

print('')
print('Bibliography')
print('------------')

for item in bibliography.bibliography():
    print(str(item))
