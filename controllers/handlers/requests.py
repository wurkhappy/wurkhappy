from base import *
from models.user import *
from controllers.verification import Verification

from datetime import datetime
import logging

class RequestAgreementHandler(BaseHandler):
	def get(self):

		empty = {
			"_xsrf": self.xsrf_token,
			"id": None,
			"name": "",
			"date": "",
			"amount": "",
			"summary": "",
			"client": None,
			"vendor": None,
			"actions": [ {
				"id": "action-request",
				"capture-id": "request-form",
				"name": "Request Agreement",
				"action": "/agreement/request.json",
				"method": "POST",
				"params": { }
			}, {
					"id": "action-cancel",
					"capture-id": "request-form",
					"name": "Cancel Request",
					"action": "/agreement/request.json",
					"method": "POST",
					"params": { }
				} ],
			"self": "vendor"
		}

		title = "New Vendor Agreement &ndash; Wurk Happy"
		self.render("agreement/request.html", title=title, data=empty)
