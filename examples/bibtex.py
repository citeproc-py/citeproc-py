

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc.source.bibtex import BibTeX

from citeproc import Citation, CitationItem


bib_style = CitationStylesStyle('harvard1.csl')
bib_source = BibTeX('xampl.bib')
bibliography = CitationStylesBibliography(bib_style, bib_source,
                                          formatter.plain)

citation1 = Citation([CitationItem('whole-collection')])
citation2 = Citation([CitationItem('whole-set'), CitationItem('misc-full')])
citation3 = Citation([CitationItem('techreport-minimal')])

bibliography.register(citation1)
bibliography.register(citation2)
bibliography.register(citation3)


def warn(citation_item):
    print("WARNING: Reference with key '{}' not found in the bibliography."
          .format(citation_item.key))

print('Citations')
print('---------')

print(bibliography.cite(citation1, warn))
print(bibliography.cite(citation2, warn))
print(bibliography.cite(citation3, warn))


print('')
print('Bibliography')
print('------------')

print(bibliography.bibliography())
