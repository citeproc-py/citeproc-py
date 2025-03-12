
import sys
import unicodedata

from . import BibliographySource, Reference
from . import Name, Date, DateRange, LiteralDate
from ..string import String, MixedString, NoCase
from .. import NAMES, DATES


class CiteProcJSON(BibliographySource):
    def __init__(self, json_data):
        for ref in json_data:
            ref_data = {}
            for key, value in ref.items():
                python_key = key.replace('-', '_')
                if python_key == 'id':
                    ref_key = str(value).lower()
                    continue
                elif python_key == 'type':
                    ref_type = value
                    continue
                elif python_key == 'key':
                    # conflicts with the ref_key, so ignore
                    continue
                if python_key == 'shortTitle':
                    python_key = 'title_short'

                if python_key in NAMES:
                    value = self.parse_names(value)
                elif python_key in DATES:
                    value = self.parse_date(value)
                elif key not in ('language', ):
                    value = self.parse_string(value)

                ref_data[python_key] = value
            self.add(Reference(ref_key, ref_type, **ref_data))

    start_tag = '<span class="nocase">'
    end_tag = '</span>'

    def parse_string(self, string):
        string = str(string)
        lower_string = string.lower()
        end = 0
        output = MixedString()
        try:
            while True:
                start = lower_string.index(self.start_tag, end)
                regular = string[end:start]
                if regular:
                    output += String(regular)
                end = lower_string.index(self.end_tag, start + 1)
                start += len(self.start_tag)
                no_case = string[start:end]
                output += NoCase(no_case)
                end += len(self.end_tag)
        except ValueError:
            regular = string[end:]
            if regular:
                output += String(regular)
        return output

    def parse_names(self, json_data):
        names = []
        for name_data in json_data:
            name = Name(**name_data)
            names.append(name)
        return names

    def parse_date(self, json_data):
        def parse_single_date(json_date):
            date_data = {}
            try:
                for i, part in enumerate(('year', 'month', 'day')):
                    date_data[part] = json_date[i]
            except IndexError:
                pass
            return date_data

        dates = []
        for json_date in json_data.get('date-parts', []):
            date = parse_single_date(json_date)
            if 'season' in json_data:
                date['season'] = json_data['season']
            dates.append(date)

        circa = json_data.get('circa', 0) != 0

        if len(dates) == 1:
            return Date(circa=circa, **dates[0])
        elif len(dates) > 1:
            return DateRange(begin=Date(**dates[0]), end=Date(**dates[1]),
                             circa=circa)
        elif 'literal' in json_data:
            return LiteralDate(json_data['literal'], circa=circa)
        else:
            return None
