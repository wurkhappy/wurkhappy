from tornado.web import UIModule
from datetime import datetime
from controllers.orm import ORMJSONEncoder

import json
import logging

class Slug(UIModule):

	def embedded_javascript(self):
		return "var slug = %s;" % json.dumps(self.slugDict, cls=ORMJSONEncoder)

	def render(self, slugDict):
		self.slugDict = slugDict
		return ''

class Navigation(UIModule):
	def render(self, data):
		return self.render_string("modules/navigation.html", data=data)

class Footer(UIModule):
	def render(self):
		return self.render_string("modules/footer.html")

class DatePicker(UIModule):
	""" Presents an HTML date picker with ISO 8601 hidden field
	"""
	def embedded_javascript(self):
		return """
actions.push(function() {{
	$('fieldset.observed select.observed').change(function(event) {{
		var $elt = $(event.target);
		var rootID = $elt.parent().attr('id');
		var name = $elt.attr('name');
		var dateParts = $('#'+rootID+'-iso').val().split("-");
		var year = dateParts[0], month = dateParts[1], day = dateParts[2];
		if (name === 'day') {{
			day = $elt.val();
		}} else if (name === 'month') {{
			month = $elt.val();
		}} else if (name === 'year') {{
			year = $elt.val();
		}}
		$('#'+rootID+' input[type=hidden]').val(year + "-" + month + "-" + day);
	}});
}});"""


	# TODO: don't hard-code the range (where to put it?)
	def render(self, pickerID, name=None, datestamp="now", yearRange=range(2011, 2025)):
		if datestamp == "now":
			datestamp = datetime.now()

		if name == None:
			name = "{0}-iso".format(pickerID)

		defaultISO = datestamp.strftime('%Y-%m-%d') if datestamp else "2011-01-01"

		return self.render_string("modules/datepicker.html",
			pickerID=pickerID,
			datestamp=datestamp,
			yearRange=yearRange,
			defaultISO=defaultISO,
			dateFieldName=name
		)