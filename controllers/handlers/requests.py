from base import *
from models.user import *
from models.request import Request
from controllers.verification import Verification
from controllers.beanstalk import Beanstalk

from datetime import datetime
import logging
from controllers import fmt
from random import randint


class RequestBase(BaseHandler):
	def assembleDictionary(self, request):
		requestDict = request.getPublicDict()

		client = User.retrieveByID(request['clientID'])
		requestDict["client"] = client.getPublicDict()

		vendor = User.retrieveByID(request['vendorID'])
		requestDict['vendor'] = vendor.getPublicDict()

		del(requestDict['clientID'])
		del(requestDict['vendorID'])

		return requestDict

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
				"id": "request-send",
				"capture-id": "request-form",
				"name": "Request Agreement",
				"action": "/agreement/request.json",
				"method": "POST",
				"params": { }
			}],
			"self": "client"
		}

		title = "New Vendor Agreement &ndash; Wurk Happy"
		self.render("agreement/request.html", title=title, data=empty)

class RequestAgreementJSONHandler(Authenticated, RequestBase):
	def post(self):
		user = self.current_user

		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('email', fmt.Enforce(str)),
					('vendorID', fmt.PositiveInteger()),
					('message', fmt.Enforce(str)),
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return

		if args['vendorID']:
			vendor = User.retrieveByID(args['vendorID'])

			if vendor and vendor['id'] == user['id']:
				error = {
					"domain": "application.conflict",
					"display": "You can't request estimates from yourself. Please choose a different vendor.",
					"debug": "'vendorID' parameter has forbidden value"
				}
				self.set_status(409)
				self.renderJSON(error)
				return

			if not vendor:
				error = {
					"domain": "resource.not_found",
					"display": "We couldn't find the vendor you specified. Could you please try that again?",
					"debug": "the 'vendorID' specified was not found"
				}
				self.set_status(400)
				self.renderJSON(error)
				return
		elif args['email']:
			vendor = User.retrieveByEmail(args['email'])

			if vendor and vendor['id'] == user['id']:
				error = {
					"domain": "application.conflict",
					"display": "You can't request estimates from yourself. Please choose a different vendor.",
					"debug": "'vendorID' parameter has forbidden value"
				}
				self.set_status(409)
				self.renderJSON(error)
				return

			if not vendor:
				profileURL = "http://media.wurkhappy.com/images/profile%d_s.jpg" % (randint(0, 5))
				vendor = User()
				vendor['email'] = args['email']
				vendor['invitedBy'] = user['id']
				vendor['profileSmallURL'] = profileURL
				
				vendor.save()
		else:
			error = {
				"domain": "web.request",
				"display": (
					'You need to specify a recipient for the request. Could '
					'you please enter a valid email address or vendor\'s name '
					'and try again?'
				),
				"debug": "missing 'vendorID' and 'email' parameters"
			}

			self.set_status(400)
			self.renderJSON(error)
			return

		request = Request()
		request['clientID'] = user['id']
		request['vendorID'] = vendor['id']
		request['message'] = args['message']
		
		request.save()
		
		# TODO: Enqueue notification!
		with Beanstalk() as bconn:
			msg = {
				'action': 'sendAgreementRequest',
				'requestID': request['id']
			}
			
			tube = self.application.configuration['notifications']['beanstalk_tube']
			bconn.use(tube)
			r = bconn.put(json.dumps(msg))
			logging.info('Beanstalk: %s#%d %s' % (tube, r, msg))
		
		self.set_status(201)
		self.renderJSON(self.assembleDictionary(request))
		return
