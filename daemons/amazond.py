# WurkHappy Amazon Payment Account Verification Daemon
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

# N.B. To get the Python interpreter to accept relative imports, this
# script must be started using the -m flag on the command line.
#
# For example:
# sudo python -m daemons.amazond --config=_b.yaml

from controllers.email import Email
from controllers.orm import Database, ORMJSONEncoder
from controllers.beanstalk import Beanstalk
from controllers.background import amazonfps
from controllers.amazonaws import AmazonS3
from daemons.base import BackgroundController, commandLineStartup

import json
import logging
import sys
import traceback



# -------------------------------------------------------------------
# The daemon process himself
# -------------------------------------------------------------------

class AmazonController (BackgroundController):
	def __init__(self, config):
		Beanstalk.configure(config['beanstalk'])
		Database.configure(config['database'])
		AmazonS3.configure(config['amazonaws'])
		
		tubeName = config['amazond']['beanstalk_tube']
		handlers = {
			'amazonTest': amazonfps.TestHandler,
			'verifyUserAccount': amazonfps.VerificationHandler,
		}
		
		super(AmazonController, self).__init__(tubeName, handlers, config)



# -------------------------------------------------------------------
# Command line startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	commandLineStartup(AmazonController, 'amazond')

