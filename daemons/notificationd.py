# WurkHappy Email Notification Daemon
# Version 0.2
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
from daemons.base import BackgroundController, commandLineStartup

import json
import logging
import sys
import traceback



# -------------------------------------------------------------------
# The daemon process himself
# -------------------------------------------------------------------

class MailController (BackgroundController):
	def __init__(self, config):
		Beanstalk.configure(config['beanstalk'])
		Database.configure(config['database'])
		Email.configure(config['smtp'])
		
		tubeName = config['notifications']['beanstalk_tube']
		handlers = {
			'beanstalkTest': notifications.TestHandler,
			
			'agreementInvite': notifications.AgreementInviteHandler,
			'agreementSent': notifications.AgreementSentHandler,
			'agreementAccepted': notifications.AgreementAcceptedHandler,
			'agreementDeclined': notifications.AgreementDeclinedHandler,
			# 'agreementUpdated': notifications.AgreementUpdatedHandler,
			'agreementWorkCompleted': notifications.AgreementWorkCompletedHandler,
			'agreementPaid': notifications.AgreementPaidHandler,
			'agreementDisputed': notifications.AgreementDisputedHandler,
			
			'sendAgreementRequest': notifications.SendAgreementRequestHandler,
			
			'userInvite': notifications.UserInviteHandler,
			'userResetPassword': notifications.UserResetPasswordHandler
		}
		
		super(MailController, self).__init__(tubeName, handlers, config)



# -------------------------------------------------------------------
# Command line startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	commandLineStartup(MailController, 'notificationd')

