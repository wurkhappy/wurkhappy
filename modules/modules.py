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
	
	def render(self, pickerID, datestamp=datetime.now()):
		return self.render_string("modules/datepicker.html", pickerID=pickerID, datestamp=datestamp)