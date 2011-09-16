from tornado.web import UIModule
from datetime import datetime
from tools.orm import ORMJSONEncoder
import json


class Slug(UIModule):
	
	def embedded_javascript(self):
		return "var slug = %s;" % json.dumps(self.slugDict, cls=ORMJSONEncoder)
	
	def render(self, slugDict):
		self.slugDict = slugDict
		return ''

class DatePicker(UIModule):
	pickerID = 0
	
	def render(self, datestamp=datetime.now()):
		self.pickerID += 1
		return self.render_string("modules/datepicker.html", pickerID=self.pickerID, datestamp=datestamp)