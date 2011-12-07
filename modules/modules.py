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
	""" Presents an HTML date picker with ISO 8601 hidden field
	"""
	def embedded_javascript(self):
		return """
actions.push(function() {{
	// var day = {datestamp.day}, month = {datestamp.month}, year = {datestamp.year};
	$('fieldset.observed select.observed').change(function(elt) {{
		return function() {{
			var $elt = $(elt);
			var name = $elt.attr('name');
			console.log("value:");
			console.log($elt.val());
			if (name === 'day') {{
				day = $elt.val();
			}} else if (name === 'month') {{
				month = $elt.val();
			}} else if (name === 'year') {{
				year = $elt.val();
			}}
			var dateString = year + "-" + month + "-" + day;
			$('#{pickerID}-iso').val(dateString);
			$('#{pickerID}-output').html(dateString);
		}}(elt);
	}});
}});"""


	# @todo: don't hard-code the range
	def render(self, pickerID, datestamp=datetime.now(), yearRange=range(2011, 2025)):
		self.pickerID = pickerID
		self.datestamp = datestamp
		defaultISO = datestamp.isoformat() if datestamp else ""
		
		return self.render_string("modules/datepicker.html", 
			pickerID=pickerID,
			datestamp=datestamp,
			yearRange=yearRange,
			defaultISO=defaultISO
		)