# WurkHappy Zipmark signup aggregation daemon
# Version 0.1
# 
# Written by Brendan Berg
# Copyright Wurk Happy, 2013

from controllers.beanstalk import Beanstalk
from controllers.background import zipmark
from controllers.orm import Database, ORMJSONEncoder
from daemons.base import BackgroundController, commandLineStartup

import json
import logging
import sys
import traceback



class ZipmarkController(BackgroundController):
	def __init__(self, config):
		Beanstalk.configure(config['beanstalk'])
		Database.configure(config['database'])

		tubeName = config['zipmarkd']['beanstalk_tube']
		handlers = {
			'zipmarkTest': zipmark.TestHandler,
			'zipmarkSignup': zipmark.SignupHandler,
			'createBill': zipmark.CreateBillHandler
		}

		super(ZipmarkController, self).__init__(tubeName, handlers, config)



# Command line startup
if __name__ == '__main__':
	commandLineStartup(ZipmarkController, 'zipmarkd')

