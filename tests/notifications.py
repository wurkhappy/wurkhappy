import tornado.template as template

import json
import os.path
from datetime import datetime

from controllers.verification import Verification
from models.agreement import Agreement
from models.user import User



class EmailNotificationTest(object):
	def __init__(self):
		self.loader = template.Loader('templates/notification')
	
	def generateHTMLOutput(self, templateName, data):
		t = self.loader.load(templateName)
		htmlString = t.generate(data=data)
		return htmlString



if __name__ == '__main__':
	# TODO: set command line args for base path, datastore
	# location and manifest location.

	def rehydrate(d):
		if '_ref' in d:
			try:
				kind, id = d['_ref'].split(':')
				return datastore.get(kind, {}).get(id, None)
			except ValueError as e:
				return None
		else:
			return d
	
	targetDir = os.path.dirname(os.path.expanduser('~/Desktop/notifications/'))
	
	datastore = json.load(open('tests/notification_data.json'))
	tests = json.load(open('tests/notification_tests.json'), object_hook=rehydrate)

	notificationTester = EmailNotificationTest()

	for test in tests:
		template = test['template']
		data = test['data']
		
		output = notificationTester.generateHTMLOutput(template, data)
		outFile = open(os.path.join(targetDir, template), 'w')
		outFile.write(output)
		outFile.close()

