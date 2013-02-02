

# http://maverick.inria.fr/~Xavier.Decoret/resources/xdkbibtex/bibtex_summary.html
# http://www.lsv.ens-cachan.fr/~markey/bibla.php?lang=en

class BibTeXEntry(dict):
    def __init__(self, document_type, attributes):
        super().__init__(attributes)
        self.document_type = document_type


class BibTeXParser(dict):
    standard_variables = {'jan': 'January'}

    def __init__(self, file_or_filename):
        try:
            self.file = open(file_or_filename, 'r')
        except TypeError:
            self.file = file_or_filename
        self.variables = {}
        self._parse(self.file)
        self.file.close()

    def _parse(self, file):
        while True:
            try:
                entry = self._parse_entry(file)
                if entry is not None:
                    entry_type, key, attributes = entry
                    self[key] = BibTeXEntry(entry_type, attributes)
            except EOFError:
                break

    def _parse_entry(self, file):
        while True:
            char = file.read(1)
            if char == '@':
                break
            elif char == '':
                raise EOFError
        entry_type = ''
        while True:
            char = file.read(1)
            if char in '{(':
                sentinel = '}' if char == '{' else ')'
                break
            entry_type += char
            if entry_type.lower().startswith('comment'):
                self._jump_to_next_line(file)
                return None
        entry_type = entry_type.strip().lower()
        if entry_type == 'string':
            name = self._parse_name(file)
            value = self._parse_value(file)
            self.variables[name] = value
            assert self._eat_whitespace(file) == sentinel
            return None
        elif entry_type == 'preamble':
            value = self._parse_value(file)
            assert self._eat_whitespace(file) == sentinel
            return None
        key = self._parse_key(file)
        entry = {}
        while True:
            name = self._parse_name(file)
            value = self._parse_value(file)
            entry[name] = value
            char = self._eat_whitespace(file)
            if char != ',':
                if char != sentinel:
                    assert char in ' \t\n\r'
                    assert self._eat_whitespace(file) == sentinel
                break
            else:
                restore_point = file.tell()
                if self._eat_whitespace(file) == sentinel:
                    break
                file.seek(restore_point)
        return entry_type.strip().lower(), key, entry

    def _parse_key(self, file):
        key = ''
        char = file.read(1)
        while char.isalnum():
            key += char
            char = file.read(1)
        if char != ',':
            assert char in ' \t\n\r'
            assert self._eat_whitespace(file) == ','
        return key.strip().lower()

    def _parse_name(self, file):
        name = ''
        char = self._eat_whitespace(file)
        while True:
            if char == '=':
                break
            name += char
            char = file.read(1)
        return name.strip().lower()

    def _parse_value(self, file):
        char = self._eat_whitespace(file)
        if char in '{"':
            value = self._parse_string(file, char)
        elif char.isalpha():
            value = self._parse_variable(file, char)
        else:
            value = self._parse_integer(file, char)

        restore_position = file.tell()
        char = self._eat_whitespace(file)
        if char == '#':
            value += self._parse_value(file)
        else:
            file.seek(restore_position)
        return value

    def _parse_string(self, file, opening_character):
        closing_character = '"' if opening_character == '"' else '}'
        string = ''
        depth = 0
        while True:
            char = file.read(1)
            if char == '{':
                depth += 1
            elif depth == 0 and char == closing_character:
                break
            elif char == '}':
                depth -= 1
            else:
                string += char
        return string

    def _parse_variable(self, file, char):
        key = ''
        restore_point = file.tell()
        while char.isalpha():
            key += char
            restore_point = file.tell()
            char = file.read(1)
        file.seek(restore_point)
        if key in self.variables:
            value = self.variables[key]
        else:
            value = self.standard_variables[key]
        return value

    def _parse_integer(self, file, char):
        integer = ''
        restore_point = file.tell()
        while char.isnumeric():
            integer += char
            restore_point = file.tell()
            char = file.read(1)
        file.seek(restore_point)
        return int(integer)

    # TODO: rename to next_token?
    def _eat_whitespace(self, file):
        char = file.read(1)
        while char in ' \t\n\r':
            char = file.read(1)
        return char

    def _jump_to_next_line(self, file):
        char = ''
        while char != '\n':
            restore_point = file.tell()
            char = file.read(1)
        file.seek(restore_point)

    def _split_name(self, name):
        pass



sample = """
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

@preamble {"This bibliography was generated on \today"}
@preamble ("This bibliography was generated on \today")

"""


if __name__ == '__main__':
    from io import StringIO

    file = StringIO(sample)
    bib = BibTeXParser(file)
    for key, entry in bib.items():
        print(key)
        for name, value in entry.items():
            print('   {}: {}'.format(name, value))
    print(bib.variables)
