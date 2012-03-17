#!/usr/bin/python

#
# Simple, naive bibtex parser
#
# Vassilios Karakoidas (2008) - vassilios.karakoidas@gmail.com
#

# bib categories
#
# @Article{
# @Book{
# @Booklet{
# @InBook{
# @InCollection{
# @InProceedings{
# @Manual{
# @MastersThesis{
# @Misc{
# @PhDThesis{
# @Proceedings{
# @TechReport{
# @Unpublished{
#

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
