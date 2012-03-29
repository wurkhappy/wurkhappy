# WurkHappy Email Notification Daemon
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

# N.B. To get the Python interpreter to accept relative imports, this
# script must be started using the -m flag on the command line.
#
# For example:
# sudo python -m daemons.notificationd --config=_b.yaml

from controllers.email import Email
from controllers.orm import Database, ORMJSONEncoder
from controllers.beanstalk import Beanstalk
from controllers.background import notifications
from controllers.background import transactions

import json
import logging
import sys
import traceback

# -------------------------------------------------------------------
# The daemon process himself
# -------------------------------------------------------------------

class TransactionController (object):
	_continue = True
	
	def __init__(self, config):
		self.config = config
		self.tubeName = config['transactions']['beanstalk_tube']
		Beanstalk.configure(config['beanstalk'])
		Database.configure(config['database'])
		Email.configure(config['smtp'])
		
		self.handlers = {
			'transactionTest': transactions.TestHandler,
			'transactionSubmitPayment': transactions.SubmitPaymentHandler
		}
	
	def start(self):
		logging.info('{"message": "Starting up..."}')
		
		with Beanstalk() as bconn:
			bconn.watch(self.tubeName)
			
			while self._continue:
				msg = bconn.reserve(timeout=15)
				
				if msg:
					logDict = {
						"jobID": msg.jid,
						"body": msg.body
					}
					
					body = None
				
					try:
						body = json.loads(msg.body)
					except ValueError as e:
						logDict['error'] = "Message body was not well-formed JSON"
						logging.error(json.dumps(logDict))
						msg.delete()
						continue
					
					if body:
						handler = self.handlers[body['action']](self)
						try:
							handler.receive(body)
							msg.delete()
						except BaseException as e:
							exc = traceback.format_exception(*sys.exc_info())
							logDict['exception'] = exc
							logging.error(json.dumps(logDict))
							msg.bury()
					else:
						logDict['error'] = "Message did not contain a body"
						logging.error(json.dumps(logDict))
						msg.delete()
		logging.info('{"message": "Successfully shut down."}')
	
	def stop(self, signum, frame):
		logging.info('{"message": "Received stop signal. Shutting down."}')
		self._continue = False



# -------------------------------------------------------------------
# Command line startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	commandLineStartup(TransactionController)

