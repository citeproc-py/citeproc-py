# Copyright (c) 2012, Vassilios Karakoidas (vassilios.karakoidas@gmail.com)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <organization> nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# based on bibparse.py from bibtex-py 0.8 by Vassilios Karakoidas
# small changes by Brecht Machiels for citeproc-py

import re
import os

from io import StringIO

class BibtexEntry:
	def __init__(self, bibfile):
		self.key = ''
		self.data = {}
		self.btype = ''
		self.data['filename'] = bibfile

	def getKey(self, key):
		if(key.lower().strip() == self.key.lower()):
			return True

		return False

	def search(self, keywords):
		for word in keywords:
			for (k, v) in self.data.items():
				try:
					v.lower().index(word.lower())
					return True
				except ValueError:
					continue

		return False

	def __get_pdf_name(self):
		if len(self.key) == 0:
			return None

		m = re.match('(.+/[^.]+)\\.bib', self.data['filename'])
		if m == None:
			return None

		filename = "%s/%s.pdf" % ( m.group(1).strip(), self.key.lower() )
		if os.access(filename, os.O_RDONLY) == 1:
			return filename

		return None

	def has_pdf(self):
		return (self.__get_pdf_name() != None)

	def export(self):
		return self.__str__()

	def totext(self):
		return

	def tohtml(self):
		return

	def __str__(self):
		result = StringIO()

		result.write("@%s{%s,\n" % ( self.btype.lower().strip(), self.key.strip() ))

		for k, v in self.data.items():
			result.write("\t%s = {%s},\n" % ( k.title().strip(), v.strip() ))

		filename =  self.__get_pdf_name()
		if filename != None:
			result.write("\tpdf-file = {%s},\n" % ( filename, ))

		result.write('}\n')

		return result.getvalue()

def parse_bib(bibfile):
	bibitems = {}
	bib_file = open(bibfile, "r")

	re_head = re.compile('@([a-zA-Z]+)[ ]*\{[ ]*(.*),')
	current = None

	for l in bib_file:
		mr = re_head.match(l.strip())
		if mr != None:
			if current == None:
				current = BibtexEntry(bibfile)
			else:
				bibitems[current.key] = current
				current = BibtexEntry(bibfile)
			current.key = mr.group(2).strip()
			current.btype = mr.group(1).strip().lower()
			continue
		try:
			l.index('=')
			kv_data = l.split('=')
			key = kv_data[0].strip()
			mr = re.search('["{](.+)["}]',kv_data[1].strip())
			if mr != None:
				current.data[key] = mr.group(1).strip()
		except (ValueError, AttributeError):
			continue

	bibitems[current.key] = current
	bib_file.close()

	return bibitems
