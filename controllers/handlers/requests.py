from base import *
from models.user import *
from controllers.verification import Verification

from datetime import datetime
import logging

class RequestAgreementHandler(BaseHandler):
	def get(self):
		self.render('agreement/request.html',
			title="Request Vendor Agreement")
