# coding: utf-8

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from citeproc.py2compat import *

from unittest import TestCase

from citeproc.source.bibtex import BibTeX
from citeproc.source.bibtex.bibtex import split_names, split_name, parse_name


class TestBibTeX(TestCase):
    def test_split_names(self):
        for names, parts in SPLIT_NAMES:
            print(names, split_names(names))
            self.assertEqual(split_names(names), parts)

    def test_split_name(self):
        for name, parts in SPLIT_NAME:
            self.assertEqual(split_name(name), parts)

    def test_parse_name(self):
        for name, reference in DECORET_NAMES:
            print('{:24}  {}'.format(name, parse_name(name)))
            self.assertEqual(parse_name(name), reference)
        for name, parts in PYBTEX_NAMES:
            reference = tuple(' '.join(pieces) if pieces else None
                              for pieces in parts)
            print('{:24}  {}'.format(name, parse_name(name)))
            self.assertEqual(parse_name(name), reference)
        for name, reference in EXTRA_NAMES:
            print('{:24}  {}'.format(name, parse_name(name)))
            self.assertEqual(parse_name(name), reference)

    def test_date_months(self):
        for january in ['jan', 'JAN', '01']:
            self.assertEqual(BibTeX._parse_month(january),
                             ({'month': 1}, ) * 2)
        self.assertEqual(BibTeX._parse_month("10~jan"),
                         ({'month': 1, 'day': 10}, ) * 2)
        self.assertEqual(BibTeX._parse_month("jul~4"),
                         ({'month': 7, 'day': 4}, ) * 2)

    def test_pages(self):
        def test(bibtex, csl):
            self.assertEqual(BibTeX._bibtex_to_csl_pages(bibtex), csl)

        test('313', '313')
        test('R112', 'R112')
        test('12+', '12')
        # page ranges
        test('1--3', '1-3')
        test('1-3', '1-3')
        test('i-iv', 'i-iv')
        test('11.1--11.27', '11.1-11.27')
        test('S43--S67', 'S43-S67')
        # Arabic letters
        test('ا-ي', 'ا-ي')


SPLIT_NAMES = [
    ('AA BB', ['AA BB']),
    ('AA and BB', ['AA', 'BB']),
    ('AA{ and }BB', ['AA{ and }BB']),
    ('AA{ }and BB', ['AA{ }and BB']),
]


SPLIT_NAME = [
    ('aa bb cc', [['aa', 'bb', 'cc']]),
    ('aa{ }bb cc', [['aa{ }bb', 'cc']]),
    ('aa{, }bb cc', [['aa{, }bb', 'cc']]),
    ('aa {bb} cc', [['aa', '{bb}', 'cc']]),
    ('aa bb, cc', [['aa', 'bb'], ['cc']]),
]


# http://maverick.inria.fr/~Xavier.Decoret/resources/xdkbibtex/bibtex_summary.html
DECORET_NAMES = [
    # name string          First        von           Last          Jr
    ( 'AA BB'          , ( 'AA'       , None        , 'BB'        , None     )),  # Testing simple case with no von.
    ( 'AA'             , (  None      , None        , 'AA'        , None     )),  # Testing that Last cannot be empty.
    ( 'AA bb'          , ( 'AA'       , None        , 'bb'        , None     )),  # Idem.
    ( 'aa'             , (  None      , None        , 'aa'        , None     )),  # Idem.
    ( 'AA bb CC'       , ( 'AA'       , 'bb'        , 'CC'        , None     )),  # Testing simple von.
    ( 'AA bb CC dd EE' , ( 'AA'       , 'bb CC dd'  , 'EE'        , None     )),  # Testing simple von (with inner uppercase words)
    ( 'AA 1B cc dd'    , ( 'AA 1B'    , 'cc'        , 'dd'        , None     )),  # Testing that digits are caseless (B fixes the case of 1B to uppercase).
    ( 'AA 1b cc dd'    , ( 'AA'       , '1b cc'     , 'dd'        , None     )),  # Testing that digits are caseless (b fixes the case of 1b to lowercase)
    ( 'AA {b}B cc dd'  , ( 'AA {b}B'  , 'cc'        , 'dd'        , None     )),  # Testing that pseudo letters are caseless.
    ( 'AA {b}b cc dd'  , ( 'AA'       , '{b}b cc'   , 'dd'        , None     )),  # Idem.
    ( 'AA {B}b cc dd'  , ( 'AA'       , '{B}b cc'   , 'dd'        , None     )),  # Idem.
    ( 'AA {B}B cc dd'  , ( 'AA {B}B'  , 'cc'        , 'dd'        , None     )),  # Idem.
    (r'AA \BB{b} cc dd', (r'AA \BB{b}', 'cc'        , 'dd'        , None     )),  # Testing that non letters are case less (in particular show how latex command are considered).
    (r'AA \bb{b} cc dd', ( 'AA'       ,r'\bb{b} cc' , 'dd'        , None     )),  # Idem.
    ( 'AA {bb} cc DD'  , ( 'AA {bb}'  , 'cc'        , 'DD'        , None     )),  # Testing that caseless words are grouped with First primilarily and then with Last.
    ( 'AA bb {cc} DD'  , ( 'AA'       , 'bb'        , '{cc} DD'   , None     )),  # Idem.
    ( 'AA {bb} CC'     , ( 'AA {bb}'  , None        , 'CC'        , None     )),  # Idem.

    ( 'bb CC, AA'      , ('AA'        , 'bb'        , 'CC'        , None     )),  # Simple case. Case do not matter for First.
    ( 'bb CC, aa'      , ('aa'        , 'bb'        , 'CC'        , None     )),  # Idem.
    ( 'bb CC dd EE, AA', ('AA'        , 'bb CC dd'  , 'EE'        , None     )),  # Testing simple von (with inner uppercase).
    ( 'bb, AA'         , ('AA'        , None        , 'bb'        , None     )),  # Testing that the Last part cannot be empty.
    ( 'BB,'            , ( None       , None        , 'BB'        , None     )),  # Testing that first can be empty after coma

    ( 'bb CC,XX, AA'   , ('AA'        , 'bb'        , 'CC'        , 'XX'     )),  # Simple Jr. Case do not matter for it.
    ( 'bb CC,xx, AA'   , ('AA'        , 'bb'        , 'CC'        , 'xx'     )),  # Idem.
    ( 'BB,, AA'        , ('AA'        , None        , 'BB'        , None     )),  # Testing that jr can be empty in between comas.

    (r"Paul \'Emile Victor"   , (r"Paul \'Emile"  , None        , "Victor", None)),
    (r"Paul {\'E}mile Victor" , (r"Paul {\'E}mile", None        , "Victor", None)),
    (r"Paul \'emile Victor"   , ( "Paul"          , r"\'emile"  , "Victor", None)),
    (r"Paul {\'e}mile Victor" , ( "Paul"          , r"{\'e}mile", "Victor", None)),

    (r"Victor, Paul \'Emile"  , (r"Paul \'Emile"  , None        , "Victor", None)),
    (r"Victor, Paul {\'E}mile", (r"Paul {\'E}mile", None        , "Victor", None)),
    (r"Victor, Paul \'emile"  , (r"Paul \'emile"  , None        , "Victor", None)),
    (r"Victor, Paul {\'e}mile", (r"Paul {\'e}mile", None        , "Victor", None)),

    ('Dominique Galouzeau de Villepin',
      ('Dominique Galouzeau', 'de'            , 'Villepin'             , None)),
    ('Dominique {G}alouzeau de Villepin',
      ('Dominique'          , '{G}alouzeau de', 'Villepin'             , None)),
    ('Galouzeau de Villepin, Dominique',
      ('Dominique'          , None            , 'Galouzeau de Villepin', None)),
]

# from Pybtex - /pybtex/tests/parse_name_test.py
PYBTEX_NAMES = [
    ('A. E.                   Siegman', (['A.', 'E.'], [], ['Siegman'], [])),
    ('A. G. W. Cameron', (['A.', 'G.', 'W.'], [], ['Cameron'], [])),
    ('A. Hoenig', (['A.'], [], ['Hoenig'], [])),
    ('A. J. Van Haagen', (['A.', 'J.', 'Van'], [], ['Haagen'], [])),
    ('A. S. Berdnikov', (['A.', 'S.'], [], ['Berdnikov'], [])),
    ('A. Trevorrow', (['A.'], [], ['Trevorrow'], [])),
    ('Adam H. Lewenberg', (['Adam', 'H.'], [], ['Lewenberg'], [])),
    ('Addison-Wesley Publishing Company',
    (['Addison-Wesley', 'Publishing'], [], ['Company'], [])),
    ('Advogato (Raph Levien)', (['Advogato', '(Raph'], [], ['Levien)'], [])),
    ('Andrea de Leeuw van Weenen',
    (['Andrea'], ['de', 'Leeuw', 'van'], ['Weenen'], [])),
    ('Andreas Geyer-Schulz', (['Andreas'], [], ['Geyer-Schulz'], [])),
    ("Andr{\\'e} Heck", (["Andr{\\'e}"], [], ['Heck'], [])),
    ('Anne Br{\\"u}ggemann-Klein', (['Anne'], [], ['Br{\\"u}ggemann-Klein'], [])),
    ('Anonymous', ([], [], ['Anonymous'], [])),
    ('B. Beeton', (['B.'], [], ['Beeton'], [])),
    ('B. Hamilton Kelly', (['B.', 'Hamilton'], [], ['Kelly'], [])),
    ('B. V. Venkata Krishna Sastry',
    (['B.', 'V.', 'Venkata', 'Krishna'], [], ['Sastry'], [])),
    ('Benedict L{\\o}fstedt', (['Benedict'], [], ['L{\\o}fstedt'], [])),
    ('Bogus{\\l}aw Jackowski', (['Bogus{\\l}aw'], [], ['Jackowski'], [])),
    ('Christina A. L.\\ Thiele',
    (['Christina', 'A.', 'L.\\'], [], ['Thiele'], [])),
    ("D. Men'shikov", (['D.'], [], ["Men'shikov"], [])),
    ("Darko \\v{Z}ubrini{\\'c}", (['Darko'], [], ["\\v{Z}ubrini{\\'c}"], [])),
    ("Dunja Mladeni{\\'c}", (['Dunja'], [], ["Mladeni{\\'c}"], [])),
    ('Edwin V. {Bell, II}', (['Edwin', 'V.'], [], ['{Bell, II}'], [])),
    ('Frank G. {Bennett, Jr.}', (['Frank', 'G.'], [], ['{Bennett, Jr.}'], [])),
    ("Fr{\\'e}d{\\'e}ric Boulanger",
    (["Fr{\\'e}d{\\'e}ric"], [], ['Boulanger'], [])),
    ('Ford, Jr., Henry', (['Henry'], [], ['Ford'], ['Jr.'])),
    ('mr Ford, Jr., Henry', (['Henry'], ['mr'], ['Ford'], ['Jr.'])),
    ('Fukui Rei', (['Fukui'], [], ['Rei'], [])),
    ('G. Gr{\\"a}tzer', (['G.'], [], ['Gr{\\"a}tzer'], [])),
    ('George Gr{\\"a}tzer', (['George'], [], ['Gr{\\"a}tzer'], [])),
    ('Georgia K. M. Tobin', (['Georgia', 'K.', 'M.'], [], ['Tobin'], [])),
    ('Gilbert van den Dobbelsteen',
    (['Gilbert'], ['van', 'den'], ['Dobbelsteen'], [])),
    ('Gy{\\"o}ngyi Bujdos{\\\'o}', (['Gy{\\"o}ngyi'], [], ["Bujdos{\\'o}"], [])),
    ('Helmut J{\\"u}rgensen', (['Helmut'], [], ['J{\\"u}rgensen'], [])),
    ('Herbert Vo{\\ss}', (['Herbert'], [], ['Vo{\\ss}'], [])),
    ("H{\\'a}n Th{\\^e}\\llap{\\raise 0.5ex\\hbox{\\'{\\relax}}}                  Th{\\'a}nh",
    (["H{\\'a}n", "Th{\\^e}\\llap{\\raise 0.5ex\\hbox{\\'{\\relax}}}"],
    [],
    ["Th{\\'a}nh"],
    [])),
    ("H{\\`a}n Th\\^e\\llap{\\raise0.5ex\\hbox{\\'{\\relax}}}                  Th{\\`a}nh",
    (['H{\\`a}n', "Th\\^e\\llap{\\raise0.5ex\\hbox{\\'{\\relax}}}"],
    [],
    ['Th{\\`a}nh'],
    [])),
    ("J. Vesel{\\'y}", (['J.'], [], ["Vesel{\\'y}"], [])),
    ("Javier Rodr\\'{\\i}guez Laguna",
    (['Javier', "Rodr\\'{\\i}guez"], [], ['Laguna'], [])),
    ("Ji\\v{r}\\'{\\i} Vesel{\\'y}",
    (["Ji\\v{r}\\'{\\i}"], [], ["Vesel{\\'y}"], [])),
    ("Ji\\v{r}\\'{\\i} Zlatu{\\v{s}}ka",
    (["Ji\\v{r}\\'{\\i}"], [], ['Zlatu{\\v{s}}ka'], [])),
    ("Ji\\v{r}{\\'\\i} Vesel{\\'y}",
    (["Ji\\v{r}{\\'\\i}"], [], ["Vesel{\\'y}"], [])),
    ("Ji\\v{r}{\\'{\\i}}Zlatu{\\v{s}}ka",
    ([], [], ["Ji\\v{r}{\\'{\\i}}Zlatu{\\v{s}}ka"], [])),
    ('Jim Hef{}feron', (['Jim'], [], ['Hef{}feron'], [])),
    ('J{\\"o}rg Knappen', (['J{\\"o}rg'], [], ['Knappen'], [])),
    ('J{\\"o}rgen L. Pind', (['J{\\"o}rgen', 'L.'], [], ['Pind'], [])),
    ("J{\\'e}r\\^ome Laurens", (["J{\\'e}r\\^ome"], [], ['Laurens'], [])),
    ('J{{\\"o}}rg Knappen', (['J{{\\"o}}rg'], [], ['Knappen'], [])),
    ('K. Anil Kumar', (['K.', 'Anil'], [], ['Kumar'], [])),
    ("Karel Hor{\\'a}k", (['Karel'], [], ["Hor{\\'a}k"], [])),
    ("Karel P\\'{\\i}{\\v{s}}ka", (['Karel'], [], ["P\\'{\\i}{\\v{s}}ka"], [])),
    ("Karel P{\\'\\i}{\\v{s}}ka", (['Karel'], [], ["P{\\'\\i}{\\v{s}}ka"], [])),
    ("Karel Skoup\\'{y}", (['Karel'], [], ["Skoup\\'{y}"], [])),
    ("Karel Skoup{\\'y}", (['Karel'], [], ["Skoup{\\'y}"], [])),
    ('Kent McPherson', (['Kent'], [], ['McPherson'], [])),
    ('Klaus H{\\"o}ppner', (['Klaus'], [], ['H{\\"o}ppner'], [])),
    ('Lars Hellstr{\\"o}m', (['Lars'], [], ['Hellstr{\\"o}m'], [])),
    ('Laura Elizabeth Jackson',
    (['Laura', 'Elizabeth'], [], ['Jackson'], [])),
    ("M. D{\\'{\\i}}az", (['M.'], [], ["D{\\'{\\i}}az"], [])),
    ('M/iche/al /O Searc/oid', (['M/iche/al', '/O'], [], ['Searc/oid'], [])),
    ("Marek Ry{\\'c}ko", (['Marek'], [], ["Ry{\\'c}ko"], [])),
    ('Marina Yu. Nikulina', (['Marina', 'Yu.'], [], ['Nikulina'], [])),
    ("Max D{\\'{\\i}}az", (['Max'], [], ["D{\\'{\\i}}az"], [])),
    ('Merry Obrecht Sawdey', (['Merry', 'Obrecht'], [], ['Sawdey'], [])),
    ("Miroslava Mis{\\'a}kov{\\'a}",
    (['Miroslava'], [], ["Mis{\\'a}kov{\\'a}"], [])),
    ('N. A. F. M. Poppelier', (['N.', 'A.', 'F.', 'M.'], [], ['Poppelier'], [])),
    ('Nico A. F. M. Poppelier',
    (['Nico', 'A.', 'F.', 'M.'], [], ['Poppelier'], [])),
    ('Onofrio de Bari', (['Onofrio'], ['de'], ['Bari'], [])),
    ("Pablo Rosell-Gonz{\\'a}lez", (['Pablo'], [], ["Rosell-Gonz{\\'a}lez"], [])),
    ('Paco La                  Bruna', (['Paco', 'La'], [], ['Bruna'], [])),
    ('Paul                  Franchi-Zannettacci',
    (['Paul'], [], ['Franchi-Zannettacci'], [])),
    ('Pavel \\v{S}eve\\v{c}ek', (['Pavel'], [], ['\\v{S}eve\\v{c}ek'], [])),
    ('Petr Ol{\\v{s}}ak', (['Petr'], [], ['Ol{\\v{s}}ak'], [])),
    ("Petr Ol{\\v{s}}{\\'a}k", (['Petr'], [], ["Ol{\\v{s}}{\\'a}k"], [])),
    ('Primo\\v{z} Peterlin', (['Primo\\v{z}'], [], ['Peterlin'], [])),
    ('Prof. Alban Grimm', (['Prof.', 'Alban'], [], ['Grimm'], [])),
    ("P{\\'e}ter Husz{\\'a}r", (["P{\\'e}ter"], [], ["Husz{\\'a}r"], [])),
    ("P{\\'e}ter Szab{\\'o}", (["P{\\'e}ter"], [], ["Szab{\\'o}"], [])),
    ('Rafa{\\l}\\.Zbikowski', ([], [], ['Rafa{\\l}\\.Zbikowski'], [])),
    ('Rainer Sch{\\"o}pf', (['Rainer'], [], ['Sch{\\"o}pf'], [])),
    ('T. L. (Frank) Pappas', (['T.', 'L.', '(Frank)'], [], ['Pappas'], [])),
    ('TUG 2004 conference', (['TUG', '2004'], [], ['conference'], [])),
    # ('TUG {\\sltt DVI} Driver Standards Committee',
    # (['TUG', '{\\sltt DVI}', 'Driver', 'Standards'], [], ['Committee'], [])),
    ('University of M{\\"u}nster',
    (['University'], ['of'], ['M{\\"u}nster'], [])),
    ('Walter van der Laan', (['Walter'], ['van', 'der'], ['Laan'], [])),
    ('Wendy G.                  McKay', (['Wendy', 'G.'], [], ['McKay'], [])),
    ('Wendy McKay', (['Wendy'], [], ['McKay'], [])),
    ('W{\\l}odek Bzyl', (['W{\\l}odek'], [], ['Bzyl'], [])),
    ('\\LaTeX Project Team', (['\\LaTeX', 'Project'], [], ['Team'], [])),
    ('\\rlap{Lutz Birkhahn}', ([], [], ['\\rlap{Lutz Birkhahn}'], [])),
    ('{Jim Hef{}feron}', ([], [], ['{Jim Hef{}feron}'], [])),
    ('{Kristoffer H\\o{}gsbro Rose}',
    ([], [], ['{Kristoffer H\\o{}gsbro Rose}'], [])),
    ('{TUG} {Working} {Group} on a {\\TeX} {Directory}                  {Structure}',
    (['{TUG}', '{Working}', '{Group}'],
    ['on', 'a'],
    ['{\\TeX}', '{Directory}', '{Structure}'],
    [])),
    ('{The \\TUB{} Team}', ([], [], ['{The \\TUB{} Team}'], [])),
    ('{\\LaTeX} project team', (['{\\LaTeX}'], ['project'], ['team'], [])),
    ('{\\NTG{} \\TeX{} future working group}',
    ([], [], ['{\\NTG{} \\TeX{} future working group}'], [])),
    ('{{\\LaTeX\\,3} Project Team}',
    ([], [], ['{{\\LaTeX\\,3} Project Team}'], [])),
    ('Johansen Kyle, Derik Mamania M.',
    (['Derik', 'Mamania', 'M.'], [], ['Johansen', 'Kyle'], [])),
]


EXTRA_NAMES = [
    ('others', (None, None, 'others', None)),
    ('Charles Louis Xavier Joseph de la Vall{\’e}e Poussin',
      ('Charles Louis Xavier Joseph', 'de la', 'Vall{\’e}e Poussin', None)),
    # the following name of the Pybtex tests doesn't agree with BibTeX's output
    # (verified using Xavier Décoret's names.bst)
    ('TUG {\\sltt DVI} Driver Standards Committee',
      ('TUG', '{\\sltt DVI}', 'Driver Standards Committee', None)),
]
