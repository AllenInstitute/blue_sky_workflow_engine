import os.path
import datetime
from django.utils import timezone
import re

class FileHolder(object):
	def load_file(self, filename):
		if self.is_valid:
			with open(filename) as f:
				self.lines = f.readlines()


	@staticmethod
	def add_color_highlighting(html):
		if html != None:
			html = re.sub(r"[^( |\)|\(|\n)]*(success)[^( |\)|\(|\n)]*", "<span class = log_s>\g<0></span>", html, flags=re.IGNORECASE)
			html = re.sub(r"[^( |\)|\(|\n)]*(warnings)[^( |\)|\(|\n)]*", "<span class = log_warn>\g<0></span>", html, flags=re.IGNORECASE)
			html = re.sub(r"[^( |\)|\(|\n|:)]*(error)[^( |\)|\(|\n|:)]*", "<span class = log_er>\g<0></span>", html, flags=re.IGNORECASE)
			html = re.sub(r"[^( |\)|\(|\n)]*(exception)[^( |\)|\(\n)]*", "<span class = log_er>\g<0></span>", html, flags=re.IGNORECASE)
			html = re.sub(r"[^( |\)|\(|\n|:)]*(failure)[^( |\)|\(|\n|:)]*", "<span class = log_er>\g<0></span>", html, flags=re.IGNORECASE)

		return html

	def get_html(self):
		html = '<p>'+ self.type_name + ' file: ' + str(self.filename) + '</p>'
		html+= '<p>Updated: ' + str(self.updated_time) + '</p>'
		if self.is_valid:
			html+= '<PRE class="log_content"><p>'
			for line in self.lines:
				html += line + '<br>'
			
			html+='</p></PRE>'
		else:
			html+='<p>This file does not exist yet.</p>'
		html+='<hr>'

		html = FileHolder.add_color_highlighting(html)

		return html

	def set_time(self, filename):
		if self.is_valid:
			self.updated_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename)).strftime('%m/%d/%Y %I:%M:%S')

	def __init__(self, filename, type_name):
		self.filename = filename
		self.is_valid = (filename != None and os.path.isfile(filename))
		self.type_name = type_name

		self.lines = []
		self.updated_time = None

		self.load_file(filename)
		self.set_time(filename)