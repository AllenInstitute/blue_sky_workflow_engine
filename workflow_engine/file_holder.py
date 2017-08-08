import os.path
import datetime
from django.utils import timezone
from django.conf import settings
import pytz
import re

ZERO = 0
ONE_MINUTES = 60

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
		if self.out_of_date:
			html+="<p class='log_er'>Warning, this file is from an older run so this file is out of date</p>"

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


	def check_out_of_date(self, start_run_time, filename):
		out_of_date = False
		if self.is_valid and start_run_time != None:
			local = pytz.timezone(settings.TIME_ZONE)
			naive = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
			local_dt = local.localize(naive, is_dst=None)
			file_date = local_dt.astimezone(pytz.utc)
			#add a one minute error margin
			file_date = file_date + datetime.timedelta(ZERO, ONE_MINUTES)
			out_of_date = file_date < start_run_time

		return out_of_date

	def __init__(self, filename, type_name, start_run_time=None):
		self.filename = filename
		self.is_valid = (filename != None and os.path.isfile(filename))
		self.type_name = type_name

		self.lines = []
		self.updated_time = None
		

		self.load_file(filename)
		self.set_time(filename)
		self.out_of_date = self.check_out_of_date(start_run_time, filename)