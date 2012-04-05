# WurkHappy Transaction Processing Daemon
# Version 0.2
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

# N.B. To get the Python interpreter to accept relative imports, this
# script must be started using the -m flag on the command line.
#
# For example:
# sudo python -m daemons.transactiond --config=_b.yaml

from controllers.email import Email
from controllers.orm import Database, ORMJSONEncoder
from controllers.beanstalk import Beanstalk
from controllers.background import transactions
from daemons.base import BackgroundController, commandLineStartup
from tornado.httpclient import HTTPClient, HTTPError
from tornado.curl_httpclient import CurlAsyncHTTPClient

import json
import logging
import sys
import traceback



# -------------------------------------------------------------------
# The daemon process himself
# -------------------------------------------------------------------

class TransactionController (BackgroundController):
	def __init__(self, config):
		Beanstalk.configure(config['beanstalk'])
		Database.configure(config['database'])
		Email.configure(config['smtp'])
		
		tubeName = config['transactions']['beanstalk_tube']
		handlers = {
			'transactionTest': transactions.TestHandler,
			'transactionSubmitPayment': transactions.SubmitPaymentHandler
		}
		
		super(TransactionController, self).__init__(tubeName, handlers, config)
		
		self.connection = HTTPClient()



# -------------------------------------------------------------------
# Command line startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	commandLineStartup(TransactionController, 'transactiond')

