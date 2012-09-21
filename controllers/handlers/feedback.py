from tornado import web
from tornado.web import HTTPError

from base import Authenticated, JSONBaseHandler
from models.user import User
from controllers import fmt
from controllers.orm import ORMJSONEncoder
from controllers.beanstalk import Beanstalk

import logging
import json



class FeedbackJSONHandler(Authenticated, JSONBaseHandler):
	@web.authenticated
	def post(self):
		user = self.current_user

		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('attemptedTask', fmt.String([None, 400])),
					('expectedResult', fmt.String([None, 400])),
					('actualResult', fmt.String([None, 400])),
					('comments', fmt.String([None, 800])),
					('discloseUser', fmt.Boolean(False))
				]
			)
		except HTTPErrorBetter as e:
			self.error_description = {
				'domain': 'web.request',
				'debug': '',
				'display': ''
			}
			
			raise HTTPError(400, 'could not parse request')

		
		message = {
			'recipient': {
				'name': 'Web Feedback',
				'email': 'contact@wurkhappy.com'
			},
			'action': 'userFeedback'
		}
		
		if args['discloseUser']:
			message['user'] = user.getPublicDict()

		if 'comments' in args:
			message['feedback'] = {
				'comments': args['comments']
			}
		elif all(k in args for k in ['attemptedTask', 'expectedResult', 'actualResult']):
			# We need all three parameters, and I can't think of a prettier way to test that.

			message['support'] = {
				'attemptedTask': args['attemptedTask'],
				'expectedResult': args['expectedResult'],
				'actualResult': args['actualResult']
			}
		else:
			self.error_description = {
				'domain': 'parameter_missing',
				'debug': (
					"missing required parameter(s) either 'comments' or "
					"'attemptedTask', 'expectedResult', and 'actualResult'"
				),
				'display': (
					"I'm sorry, we didn't recieve your input for all of the "
					"fields required to submit feedback. Would you please "
					"review the form and try again?"
				)
			}
			
			raise HTTPError(400, 'missing required parameters')

		with Beanstalk() as bconn:
			tubeName = self.application.configuration['notifications']['beanstalk_tube']
			bconn.use(tubeName)
			r = bconn.put(json.dumps(message, cls=ORMJSONEncoder))
			logging.info('Beanstalk: {0}#{1} {2}'.format(tubeName, r, message))

