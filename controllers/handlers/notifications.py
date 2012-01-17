from __future__ import division

from base import BaseHandler
from models.user import User, UserPrefs
from controllers import fmt
from controllers.beanstalk import Beanstalk
import tornado.web as web

import json
import logging
import os

from datetime import datetime


class NotificationHandler(BaseHandler):
	
	@web.authenticated
	@web.asynchronous
	def get(self):
		user = self.current_user
		
		with Beanstalk() as bconn:
			bconn.listen('user:{0}'.format(user.id))
			bconn.reserve(callback=self.beanstalkDidReserveJob)
	
	def beanstalkDidReserveJob(self, msg):
		user = self.current_user
		
		error = {
			'domain': 'notification.queue',
			'display': 'The server could not understand the current message.'
		}
		
		if msg:
			logDict = {
				'jobID': msg.jid,
				'body': msg.body
			}
			
			body = None
			
			try:
				body = json.loads(msg.body)
			except ValueError as e:
				logDict['error'] = "Message body was not well-formed JSON"
				logging.error(json.dumps(logDict))
				
				error['debug'] = 'malformed message body'
				self.renderJSON(error)
			
			if not body:
				logDict['error'] = "Message body was empty"
				logging.error(json.dumps(logDict))
				
				error['debug'] = 'empty message body'
				self.renderJSON(error)
			else:
				fromUser = User.retrieveByID(body['from'])
				
				if not fromUser:
					logDict['error'] = "Not from valid user"
					logging.error(json.dumps(logDict))
					
					error['debug'] = "Not from valid user"
					self.renderJSON(error)
				else:
					response = {
						'to': user.publicDict(),
						'from': fromUser.publicDict(),
						'text': body['text'],
					}
					
					if 'entities' in body:
						response['entities'] = body['entities']
					
					self.renderJSON(response)
			
			msg.delete()
		
		else:
			logging.error('{"error":"Call to beanstalkDidReserveJob without a job"}')
			error['debug'] = 'response from server with no job'
			self.renderJSON(error)
		
		self.finish()
