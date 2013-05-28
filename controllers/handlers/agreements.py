from __future__ import division

import tornado.web as web
from base import (
	BaseHandler,
	JSONBaseHandler,
	Authenticated,
	CookieAuthenticated, 
	TokenAuthenticated
)
from models.user import *
from models.agreement import *
from models.request import Request
from models.transaction import Transaction, AmazonTransaction
from models.paymentmethod import (
	UserPayment, PaymentBase, OOBPaymentMethod, AmazonPaymentMethod, ZipmarkPaymentMethod
)
from controllers import fmt
from controllers.orm import ORMJSONEncoder
from controllers.beanstalk import Beanstalk
from controllers.amazonaws import AmazonFPS
from controllers.application import WurkHappy

from collections import defaultdict
from datetime import datetime
from random import randint
import urlparse
import urllib
import hashlib
import logging
import re



class AgreementBase(object):
	def assembleDictionary(self, agreement):
		# This should probably go in the model class, but it
		# could be considered controller, so it's here for now.

		agreementDict = agreement.getPublicDict()

		client = User.retrieveByID(agreement['clientID']) if agreement['clientID'] else None
		agreementDict['client'] = client and client.getPublicDict()

		vendor = User.retrieveByID(agreement['vendorID'])
		agreementDict['vendor'] = vendor.getPublicDict()

		del(agreementDict['clientID'])
		del(agreementDict['vendorID'])

		agreementDict['phases'] = []

		for phase in AgreementPhase.iteratorWithAgreementID(agreement['id']):
			agreementDict['phases'].append(phase.getPublicDict())

		return agreementDict



# -------------------------------------------------------------------
# Profile (Add / Edit)
# -------------------------------------------------------------------

class AgreementListHandler(Authenticated, BaseHandler):

	@web.authenticated
	def get(self, withWhom):
		user = self.current_user
		# userDwolla = UserDwolla.retrieveByUserID(user['id'])
		
		templateDict = {
			"_xsrf": self.xsrf_token,
			"userID": user['id']
			# "paymentEnabled": True if userDwolla else False
		}

		if withWhom.lower() == 'clients':
			agreementType = 'Client'
			agreements = Agreement.iteratorWithVendorID(user['id'])
			templateDict['agreementCount'] = Agreement.countWithVendorID(user['id'])
			templateDict['aggregateCost'] = Agreement.costStringWithVendorID(user['id'])
			templateDict['self'] = 'vendor'
		elif withWhom.lower() == 'vendors':
			agreementType = 'Freelance'
			agreements = Agreement.iteratorWithClientID(user['id'])
			templateDict['agreementCount']  = Agreement.countWithClientID(user['id'])
			templateDict['aggregateCost']  = Agreement.costStringWithClientID(user['id'])
			templateDict['self'] = 'client'
		else:
			self.set_status(403)
			self.write("Forbidden")
			return

		# agreementList = []

		actionItems = []
		awaitingReply = []
		inProgress = []

		def appendAgreement(lst, agr, usr):
			lst.append({
				"id": agr['id'],
				"name": agr['name'],
				"other_id": usr and usr['id'],
				"other_name": usr and usr.getFullName(),
				"date": agr['dateCreated'].strftime('%B %d, %Y'),
				"amount": agr.getCostString(),
				"profileURL": usr and (usr['profileSmallURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg'),
				# Default profile photo? Set during signup?
				"state": agr.getCurrentState().__class__.__name__,
			})

		for agreement in agreements:
			state = agreement.getCurrentState()
			
			if isinstance(state, InvalidState):
				logging.error('Agreement %d (vendor: %d, client: %d) is invalid' % (
						agreement['id'], agreement['vendorID'], agreement['clientID']
					)
				)
			
			
			if agreementType == 'Client':
				other = User.retrieveByID(agreement['clientID']) if agreement['clientID'] else None
				
				if isinstance(state, (DraftState, DeclinedState, ContestedState)):
					appendAgreement(actionItems, agreement, other)
				elif isinstance(state, (EstimateState, CompletedState)):
					appendAgreement(awaitingReply, agreement, other)
				elif isinstance(state, (InProgressState)):
					appendAgreement(inProgress, agreement, other)
				elif isinstance(state, PaidState):
					templateDict['agreementCount'] -= 1
			else:
				other = User.retrieveByID(agreement['vendorID'])

				if isinstance(state, (EstimateState, CompletedState)):
					appendAgreement(actionItems, agreement, other)
				elif isinstance(state, (DeclinedState, ContestedState)):
					appendAgreement(awaitingReply, agreement, other)
				elif isinstance(state, InProgressState):
					appendAgreement(inProgress, agreement, other)
				elif isinstance(state, PaidState):
					templateDict['agreementCount'] -= 1

		templateDict['agreementType'] = agreementType
		templateDict['agreementGroups'] = []

		for (name, lst) in [
			("Requires Attention", actionItems),
			("Waiting for %s" % agreementType, awaitingReply),
			("In Progress", inProgress)]:

			if len(lst):
				templateDict['agreementGroups'].append((name, lst))

		title = "%s Agreements &ndash; Wurk Happy" % agreementType
		self.render("agreement/list.html", title=title, data=templateDict)


class AgreementHandler(TokenAuthenticated, BaseHandler, AgreementBase, AmazonFPS):
	buttonTable = {
		'vendor': defaultdict(lambda: [], {
			DraftState: [
				('action-save', 'Save as Draft'),
				('action-send', 'Send Agreement')
			],
			DeclinedState: [
				('action-save', 'Save Changes'),
				('action-resend', 'Re-send Agreement')
			],
			InProgressState: [
				('action-markcomplete', 'Mark Phase Complete')
			],
			ContestedState: [
				('action-markcomplete', 'Mark Phase Complete')
			]
		}),
		'client': defaultdict(lambda: [], {
			EstimateState: [
				('action-accept', 'Accept Agreement'),
				('action-decline', 'Request Changes')
			],
			CompletedState: [
				('action-verify', 'Verify and Pay'),
				('action-dispute', 'Dispute')
			]
		})
	}
	
	# @web.authenticated
	# TODO: SECURITY AUDIT
	@web.authenticated
	def get(self, agreementID=None):
		user = self.current_user
		agreement = None
		
		if self.token:
			logging.warn(self.request.arguments)
			
			if user['password'] is None:
				
				userDict = {
					'_xsrf': self.xsrf_token,
					'token': self.token,
					'id': user['id'],
					'firstName': user['firstName'],
					'lastName': user['lastName'],
					'fullName': user.getFullName(),
					'email': user['email'],
					'telephone': user['telephone'] or '',
					'profileURL': [
						user['profileSmallURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg',
						user['profileLargeURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg'
					],
					'password': False,
					'dwolla': {
						'dwollaID': None,
						'authorizeURL': ''
					},
					'redirectURL': '{0}://{1}{2}'.format(self.request.protocol, WurkHappy.getSettingWithTag('hostname'), self.request.uri)
				}
				
				self.render('user/quickstart.html', title='Welcome to Wurk Happy', data=userDict)
				return
		
		if not agreementID:
			# Must have been routed from /agreement/new
			title = "New Agreement &ndash; Wurk Happy"
			
			try:
				args = fmt.Parser(self.request.arguments,
					optional=[
						('request', fmt.PositiveInteger())
					]
				)
			except fmt.HTTPErrorBetter as e:
				logging.warn(e.__dict__)
				self.set_status(e.status_code)
				self.write(e.body_content)
				return
			
			empty = {
				"_xsrf": self.xsrf_token,
				"id": None,
				"name": "",
				"date": "",
				"amount": "",
				"summary": "",
				"client": None,
				"vendor": user.getPublicDict(),
				"phases": [],
				"state": 'DraftState',
				"actions": [
					('action-save', 'Save as Draft'),
					('action-send', 'Send Agreement')
				],
				"self": "vendor"
			}
			
			# Pre-populate data from a client request.
			
			request = args['request'] and Request.retrieveByID(args['request'])
			
			if request and request['vendorID'] == user['id']:
				client = User.retrieveByID(request['clientID'])
				empty['request'] = request.getPublicDict()
				empty['client'] = client and client.getPublicDict()
			
			# Modify behavior to prompt for Amazon configuration if no
			# confirmation is on file.
			
			paymentMethod = PaymentBase.retrieveDefaultByUserID(user['id'])
			empty['paymentMethod'] = paymentMethod and paymentMethod.getPublicDict()

			if paymentMethod and paymentMethod.canReceivePayment():
				empty['paymentMethodStatus'] = 'verified'
			elif paymentMethod is not None:
				empty['paymentMethodStatus'] = 'pending'
				# TODO: Replace below with generalized form
				empty['actions'][1] = ('action-amazon-verify', 'Send Agreement')
			else:
				empty['paymentMethodStatus'] = None
				# TODO: Replace below with generalized form
				empty['actions'][1] = ('action-amazon-prompt', 'Send Agreement')

			self.render("agreement/edit.html", title=title, data=empty, json=lambda x: json.dumps(x, cls=ORMJSONEncoder))
			return

		agreement = agreement or Agreement.retrieveByID(agreementID)
		phases = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))

		if not agreement:
			self.set_status(404)
			self.write("Not Found")
			return

		# Capture return data from an Amazon pay pipeline
		# paymentReason
		# signatureMethod
		# transactionAmount
		# status
		# referenceId
		# recipientEmail
		# transactionDate
		# operation
		# recipientName
		# signatureVersion
		# certificateUrl
		# paymentMethod
		# signature

		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('status', fmt.Enforce(str)),
					('referenceId', fmt.Enforce(str)),
					('transactionDate', fmt.PositiveInteger()),
					('transactionAmount', fmt.Enforce(str)),
					('transactionId', fmt.Enforce(str)),
					('paymentMethod', fmt.Enforce(str))
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			return
		
		# Before we handle the potential query args from Amazon, we need to
		# build up the agreement's vendor and client info and current state.
		
		if agreement['vendorID'] == user['id']:
			agreementType = 'Client'
		elif agreement['clientID'] == user['id']:
			state = agreement.getCurrentState()

			if isinstance(state, (DraftState, InvalidState)):
				logging.error('Agreement %d (vendor: %d, client: %d) is invalid' % (
						agreement['id'], agreement['vendorID'], agreement['clientID']
					)
				)
				self.set_status(404)
				self.write("Not found")
				return
			agreementType = 'Vendor'
		else:
			self.set_status(403)
			self.write("Forbidden")
			return
		
		currentState = agreement.getCurrentState()
		currentPhase = agreement.getCurrentPhase()

		# Now we handle any potential query arguments.
		
		if args['status'] is not None:
			signatureIsValid = self.verifySignature('{0}://{1}{2}'.format(
					self.request.protocol,
					WurkHappy.getSettingWithTag('hostname'),
					self.request.path
				),
				self.request.query,
				self.application.configuration['amazonaws']
			)

			if not (signatureIsValid or self.application.configuration['tornado'].get('debug') == True):
				logging.error("Bad Amazon payments response payload\n%s", self.request.query)
			else:
				# '{0}.{1}'.format(phaseID, uniquingAgent)
				phaseID, reference = args['referenceId'].split('.')
				
				if currentPhase and currentPhase['id'] != phaseID:
					logging.error('Current phase does not match phase in Amazon callback.')
				
				transaction = Transaction.retrieveByTransactionReference(reference)

				if not transaction:
					transaction = Transaction(
						transactionReference=reference,
						senderID=agreement['clientID'],
						recipientID=agreement['vendorID']
					)
					
					if args['transactionDate']:
						transaction['dateInitiated'] = datetime.fromtimestamp(args['transactionDate'])

				if not transaction['amount'] and args['transactionAmount']:
					currencyParser = fmt.Currency()
					transaction['amount'] = currencyParser.filter(args['transactionAmount'].replace('USD','').strip())

				if not transaction['agreementPhaseID']:
					transaction['agreementPhaseID'] = phaseID

				if not (transaction['senderID'] and transaction['recipientID']):
					transaction['senderID'] = agreement['clientID']
					transaction['recipientID'] = agreement['vendorID']

				amzTxn = None

				if args['status'] == 'PS':
					transaction['dateApproved'] = datetime.now()
					
					amzTxn = AmazonTransaction(
						amazonTransactionID=args['transactionId'],
						amazonPaymentMethod=args['paymentMethod']
					)

					logging.info('State before state change due to Amazon callback: %s', currentState)

					# If the transaction was approved, update the agreement state
					# (This should have some more granularity. Ugh.)
					unsavedRecords = []

					try:
						currentState = currentState.performTransition('client', 'verify', unsavedRecords, phase=currentPhase)
					except StateTransitionError as e:
						pass

					logging.info('State after state change due to Amazon callback: %s', currentState)

					for record in unsavedRecords:
						record.save()
				elif args['status'] in ['ME', 'PF', 'SE']:
					transaction['dateDeclined'] = datetime.now()
					logging.error("Transaction declined by Amazon\n%s", transaction)

				transaction.save()
				amzTxn['transactionID'] = transaction['id']
				amzTxn.save()
			
			# We do this here, but it would be prettier if we did this using a JavaScript pushState
			self.redirect('{0}://{1}{2}'.format(self.request.protocol, WurkHappy.getSettingWithTag('hostname'), self.request.path))
			return


		# The agreement data gets wrapped up in a dictionary for
		# the template. This contains name, date, and amount of
		# the agreement, as well as terms, transaction dates, and
		# relationships.
		#
		# {
		#     "id": 123
		#     "name": "Marketing Outline",
		#     "date": "January 1, 2010",
		#     "amount": "$1,300.52",
		#     "client": {
		#         "id": 1,
		#         "fullName": "Cindy Jones",
		#         "profileURL": "http://media.wurkhappy.com/eW5no...s.png"
		#     },
		#     "vendor": {
		#         "id": 17,
		#         "fullName": "Greg Smith",
		#         "profileURL": "http://media.wurkhappy.com/EKveW...s.png"
		#     },
		#     "self": "client",
		#     "other": "vendor",
		#     "transactions": [{
		#             "user": "client",
		#             "type": "Sent by ",
		#             "date": "January 1, 2010"
		#         }, {
		#             "user": "vendor",
		#             "type": "Approved by ",
		#             "date": "January 3, 2010"
		#         }],
		#     "phases": [{
		#             "amount": "2,500.00",
		#             "estDateCompleted": "August 1, 2011",
		#             "dateCompleted": "August 1, 2011,
		#             "description": "Lorem ipsum dolor..."
		#         }, {
		#             "amount": "1,500.00",
		#             "estDateCompleted": "August 15, 2011",
		#             "dateCompleted": None,
		#             "description": "Sit amet hoc infinitim...",
		#             "comments": "Bacon mustache fixie PBR..."
		#     }],
		#     "actions": [
		#         ("action-accept", "Accept Agreement"),
		#         ("action-decline", "Request Changes")
		#     ]
		# }

		templateDict = {
			"_xsrf": self.xsrf_token,
			"id": agreement['id'],
			"name": agreement['name'],
			"date": agreement['dateCreated'].strftime('%B %d, %Y'),
			"amount": agreement.getCostString(),
		}
		
		summary = AgreementSummary.retrieveByAgreementID(agreement['id'])

		if summary:
			templateDict['summary'] = summary['summary'] or ''
			templateDict['summaryComments'] = summary['comments'] or ''
		else:
			templateDict['summary'] = None
			templateDict['summaryComments'] = ''

		if agreementType == 'Client':
			client = User.retrieveByID(agreement['clientID']) if agreement['clientID'] else None
			templateDict["client"] = client and client.getPublicDict()
			templateDict["vendor"] = user.getPublicDict()
			templateDict["self"] = "vendor"
			templateDict["other"] = "client"
		else:
			vendor = User.retrieveByID(agreement['vendorID'])
			templateDict["client"] = user.getPublicDict()
			templateDict["vendor"] = vendor.getPublicDict()
			templateDict["self"] = "client"
			templateDict["other"] = "vendor"


		# Add the agreement phase data to the template dict

		templateDict["phases"] = []

		for phase in phases:

			phaseDict = {
				"amount": phase.getCostString(),
				"description": phase['description'],
				"estDateCompleted": phase['estDateCompleted'],
				"dateCompleted": phase['dateCompleted'],
				"dateVerified": phase['dateVerified'],
				"dateContested": phase['dateContested']
			}

			if phase['comments']:
				phaseDict["comments"] = phase['comments']

			if currentPhase and phase['id'] == currentPhase['id']:
				phaseDict["isCurrent"] = True

			templateDict["phases"].append(phaseDict)

		templateDict["amount"] = agreement.getCostString()

		if currentPhase:
			templateDict["currentPhase"] = {
				"amount": currentPhase.getCostString(),
				"phaseID": currentPhase['id'],
				"phaseNumber": currentPhase['phaseNumber'],
				"description": currentPhase['description']
			}

		# Transactions are datetime properties of the agreement.

		transactions = [{
			"type": "Sent by ",
			"user": "vendor",
			"date": agreement['dateCreated'].strftime('%B %d, %Y')
		}]

		if agreement['dateDeclined']:
			transactions.append({
				"type": "Declined by ",
				"user": "client",
				"date": agreement['dateDeclined'].strftime('%B %d, %Y')
			})

		if agreement['dateModified']:
			transactions.append({
				"type": "Modified by ",
				"user": "vendor",
				"date": agreement['dateModified'].strftime('%B %d, %Y')
			})

		if agreement['dateAccepted']:
			transactions.append({
				"type": "Accepted by ",
				"user": "client",
				"date": agreement['dateAccepted'].strftime('%B %d, %Y')
			})

		if currentPhase and currentPhase['dateCompleted']:
			transactions.append({
				"type": "Completed by ",
				"user": "vendor",
				"date": currentPhase['dateCompleted'].strftime('%B %d, %Y')
			})

		if currentPhase and currentPhase['dateVerified']:
			transactions.append({
				"type": "Verified and paid by ",
				"user": "client",
				"date": currentPhase['dateVerified'].strftime('%B %d, %Y')
			})

		templateDict['transactions'] = transactions

		templateDict['state'] = currentState.__class__.__name__
		
		# Look for the user's Dwolla account. If there is none, direct the
		# user to the Payment Information tab. Otherwise, render the buttons.
		
		# userDwolla = UserDwolla.retrieveByUserID(user['id'])
		
		# if not userDwolla:
		# 	templateDict['actions'] = [
		# 		('action-connect', 'Connect an Account')
		# 	]
		# else:
		templateDict['actions'] = list(self.buttonTable[templateDict['self']][currentState.__class__])
		
		title = "%s Agreement: %s &ndash; Wurk Happy" % (agreementType, agreement['name'])
		
		# We use the presence of the recipient email key to selectively render the Amazon button UI module.
		if templateDict['self'] == 'client' and isinstance(currentState, CompletedState):
			paymentMethod = PaymentBase.retrieveDefaultByUserID(vendor['id'])
			logging.info(paymentMethod)
			templateDict['vendorPaymentMethod'] = paymentMethod
		
		# Modify behavior to prompt for Amazon configuration if no
		# confirmation is on file.
		
		if agreement['vendorID'] == user['id']:
			templateDict['uri'] = self.request.uri

			paymentMethod = PaymentBase.retrieveDefaultByUserID(user['id'])
			templateDict['paymentMethod'] = paymentMethod and paymentMethod.getPublicDict()
			
			if paymentMethod and paymentMethod.canReceivePayment():
				templateDict['paymentMethodStatus'] = 'verified'
			elif paymentMethod is not None:
				templateDict['paymentMethodStatus'] = 'pending'
				# TODO: Replace below with generalized form
				if isinstance(currentState, (DraftState, DeclinedState)):
					if len(templateDict['actions']) > 1:
						templateDict['actions'][1] = ('action-amazon-verify', 'Send Agreement')
				elif isinstance(currentState, (InProgressState, ContestedState)):
					if len(templateDict['actions']) >= 1:
						templateDict['actions'][0] = ('action-amazon-verify', 'Mark Phase Complete')
			else:
				templateDict['paymentMethodStatus'] = None
				# TODO: Replace below with generalized form
				if isinstance(currentState, (DraftState, DeclinedState)):
					if len(templateDict['actions']) > 1:
						templateDict['actions'][1] = ('action-amazon-prompt', 'Send Agreement')
				elif isinstance(currentState, (InProgressState, ContestedState)):
					if len(templateDict['actions']) >= 1:
						templateDict['actions'][0] = ('action-amazon-prompt', 'Mark Phase Complete')

			if isinstance(currentState, (DraftState, DeclinedState)):
				self.render("agreement/edit.html",
					title=title, data=templateDict,
					json=lambda x: json.dumps(x, cls=ORMJSONEncoder)
				)
			else:
				self.render("agreement/detail.html",
					title=title, data=templateDict,
					json=lambda x: json.dumps(x, cls=ORMJSONEncoder)
				)
		else:
			self.render("agreement/detail.html",
				title=title, data=templateDict,
				json=lambda x: json.dumps(x, cls=ORMJSONEncoder)
			)



class NewAgreementJSONHandler(CookieAuthenticated, JSONBaseHandler, AgreementBase):
	@JSONBaseHandler.authenticated
	def post(self, action):
		user = self.current_user

		logging.warn(self.request.arguments)

		agreement = Agreement()
		agreement['vendorID'] = user['id']
		
		agreementText = None

		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('title', fmt.Enforce(str)),
					('email', fmt.Enforce(str)),
					('clientID', fmt.PositiveInteger()),
					('summary', fmt.Enforce(str)),
					('cost', fmt.List(fmt.Currency([100, 1000000]))),
					('details', fmt.List(fmt.Enforce(str))),
					('estDateCompleted', fmt.List(fmt.Enforce(str))),
					('date', fmt.List(fmt.Date()))
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return

		agreement['name'] = args['title']

		if args['clientID']:
			client = User.retrieveByID(args['clientID'])

			if client and client['id'] == user['id']:
				error = {
					"domain": "application.conflict",
					"display": "You can't send estimates to yourself. Please choose a different client.",
					"debug": "'clientID' parameter has forbidden value"
				}
				self.set_status(409)
				self.renderJSON(error)
				return

			if not client:
				error = {
					"domain": "resource.not_found",
					"display": "We couldn't find the client you specified. Could you please try that again?",
					"debug": "the 'clientID' specified was not found"
				}
				self.set_status(400)
				self.renderJSON(error)
				return
		elif args['email']:
			client = User.retrieveByEmail(args['email'])

			if client and client['id'] == user['id']:
				error = {
					"domain": "application.conflict",
					"display": "You can't send estimates to yourself. Please choose a different client.",
					"debug": "'clientID' parameter has forbidden value"
				}
				self.set_status(409)
				self.renderJSON(error)
				return

			if not client:
				profileURL = "https://s3.amazonaws.com/media.wurkhappy.com/images/profile%d_s.jpg" % (randint(0, 4))
				client = User()
				client['email'] = args['email']
				client['invitedBy'] = user['id']
				client['dateCreated'] = datetime.now()
				client['profileSmallURL'] = profileURL
				
				client.save()
		else:
			client = None

		agreement['clientID'] = client and client['id']
		logging.warn(agreement)
		
		summary = AgreementSummary(summary=args['summary'])

		phases = []
		for num, (cost, descr, date) in enumerate(zip(args['cost'], args['details'], args['date'])):
			phase = AgreementPhase(
				phaseNumber=num,
				amount=cost,
				description=descr,
				estDateCompleted=date
			)
			phases.append(phase)

		# TODO: CHECK CLIENT ID AND PHASE LENGTH BY TRIGGERING A STATE TRANSITION FOR SENDING

		if action == "send":
			clientState = client.getCurrentState()
			
			if isinstance(clientState, (
					PendingUserState, NewUserState, InvitedUserState, BetaUserState)):
				clientState.performTransition("send_verification", {})
				
				msg = dict(
					userID=client['id'],
					action='agreementInvite'
				)
			elif isinstance(clientState, ActiveUserState):
				msg = dict(
					userID=client['id'],
					action='agreementSent'
				)
			else:
				msg = dict()
			
			agreement['dateSent'] = datetime.now()

		agreement.save()
		
		summary['agreementID'] = agreement['id']
		summary.save()
		
		for phase in phases:
			phase['agreementID'] = agreement['id']
			phase.save()

		logging.warn(agreement)
		logging.warn(phases)
		
		if action == "send" and 'action' in msg:
			msg['agreementID'] = agreement['id']
			
			with Beanstalk() as bconn:
				tube = self.application.configuration['notifications']['beanstalk_tube']
				bconn.use(tube)
				r = bconn.put(json.dumps(msg))
				logging.info('Beanstalk: {0}#{1} {2}'.format(tube, r, msg))
		
		self.set_status(201)
		self.set_header('Location', 'http://' + self.request.host + '/agreement/' + str(agreement['id']) + '.json')
		self.renderJSON(self.assembleDictionary(agreement))



class AgreementJSONHandler(Authenticated, JSONBaseHandler, AgreementBase):

	@JSONBaseHandler.authenticated
	def get(self, agreementID):
		user = self.current_user

		agreement = Agreement.retrieveByID(agreementID)

		if not agreement:
			self.error_description = {
				"domain": "resource.not_found",
				"display": (
					"We couldn't find the agreement you specified. "
					"Could you please try that again?"
				),
				"debug": "the 'agreementID' specified was not found"
			}
			raise web.HTTPError(404, "AgreementID not found")

		if agreement['vendorID'] != user['id'] and agreement['clientID'] != user['id']:
			self.error_description = {
				"domain": "resource.forbidden",
				"display": (
					"You are not authorized to view this agreement."
				),
				"debug": "the 'agreementID' specified is forbidden"
			}
			raise web.HTTPError(403, "Attempt to view unauthorized agreement")

		self.renderJSON(self.assembleDictionary(agreement))



class AgreementStatusJSONHandler(Authenticated, JSONBaseHandler, AgreementBase):

	@JSONBaseHandler.authenticated
	def get(self, agreementID):
		user = self.current_user

		agreement = Agreement.retrieveByID(agreementID)

		if not agreement:
			self.error_description = {
				"domain": "resource.not_found",
				"display": (
					"We couldn't find the agreement you specified. "
					"Could you please try that again?"
				),
				"debug": "the 'agreementID' specified was not found"
			}
			raise web.HTTPError(404, "AgreementID not found")

		if agreement['vendorID'] != user['id'] and agreement['clientID'] != user['id']:
			self.error_description = {
				"domain": "resource.forbidden",
				"display": (
					"You are not authorized to view this agreement."
				),
				"debug": "the 'agreementID' specified is forbidden"
			}
			raise web.HTTPError(403, "Attempt to view unauthorized agreement")

		stateDict = {
			"agreement": {
				"id": agreement['id']
			},
			"state": agreement.getCurrentState()
		}

		self.renderJSON(stateDict)



class AgreementActionJSONHandler(CookieAuthenticated, JSONBaseHandler, AgreementBase):

	@JSONBaseHandler.authenticated
	def post(self, agreementID, action):
		'''POST handler for /agreement/([0-9]+)/(save|send|accept|decline|mark_complete|verify|dispute)\.json'''
		
		user = self.current_user

		agreement = Agreement.retrieveByID(agreementID)

		if not agreement:
			self.error_description = {
				'domain': 'resource.not_found',
				'display': (
					"We couldn't find the agreement you specified. "
					"Could you please try that again?"
				),
				'debug': "the 'agreementID' specified was not found"
			}
			raise web.HTTPError(404, "AgreementID not found")

		if agreement['vendorID'] != user['id'] and agreement['clientID'] != user['id']:
			self.error_description = {
				'domain': 'resource.forbidden',
				'display': (
					"You are not authorized to view this agreement."
				),
				'debug': "the 'agreementID' specified is forbidden"
			}
			raise web.HTTPError(403, "Attempt to view unauthorized agreement")

		agreementText = None

		role = "vendor" if agreement['vendorID'] == user['id'] else "client"

		currentState = agreement.getCurrentState()
		currentPhase = agreement.getCurrentPhase()

		# In order to make sure records are not put in inconsistent states, a
		# list of unsaved records is maintained so records can be saved
		# en masse after a successful state transition. Otherwise, no change
		# occurs.

		unsavedRecords = []

		# Because of a change to the way we model agreement states (more
		# specifically the transitions between them), we're packing up a data
		# object that gets passed to the performTransition() function.

		# If role is vendor, make changes to the agreement before modifying
		# the agreement's state. That way, if the state transition is invalid
		# the changes to the agreement record won't be saved.

		if role == "vendor":
			try:
				args = fmt.Parser(self.request.arguments,
					optional= [
						('title', fmt.Enforce(str)),
						('email', fmt.Enforce(str)),
						('clientID', fmt.PositiveInteger()),
						('summary', fmt.Enforce(str)),
						('cost', fmt.List(fmt.Currency([100, 1000000]))),
						('details', fmt.List(fmt.Enforce(str))),
						('estDateCompleted', fmt.List(fmt.Enforce(str))),
						('date', fmt.List(fmt.Date()))
					]
				)
			except fmt.HTTPErrorBetter as e:
				self.error_description = json.loads(e.body_content)
				self.error_description['display'] = "The request parameters were malformed"
				raise web.HTTPError(400)

			if isinstance(currentState, DraftState):
				client = None

				# The agreement ....
				if args['clientID']:
					client = User.retrieveByID(args['clientID'])

					if not client:
						self.error_description = {
							"domain": "resource.not_found",
							"display": (
								"We couldn't find the client you specified. "
								"Could you please try that again?"
							),
							"debug": "the 'clientID' specified was not found"
						}
						raise web.HTTPError(400, "ClientID not found")

					agreement['clientID'] = client['id']
				elif args['email']:
					client = User.retrieveByEmail(args['email'])

					if client and client['id'] == user['id']:
						self.error_description = {
							"domain": "application.conflict",
							"display": "You can't send estimates to yourself. Please choose a different client.",
							"debug": "'clientID' parameter has forbidden value"
						}
						raise web.HTTPError(409, "Can't send estimates to self")

					if not client:
						profileURL = "http://media.wurkhappy.com/images/profile%d_s.jpg" % (randint(0, 4))
						client = User()
						client['email'] = args['email']
						client['invitedBy'] = user['id']
						client['dateCreated'] = datetime.now()
						client['profileSmallURL'] = profileURL
						
						client.save()
					
					agreement['clientID'] = client['id']


			if (isinstance(currentState, DraftState) or
					isinstance(currentState, EstimateState) or
					isinstance(currentState, DeclinedState)):

				agreement['name'] = args['title'] or agreement['name']

				summary = AgreementSummary.retrieveByAgreementID(agreement['id'])

				if not summary:
					summary = AgreementSummary(agreementID=agreement['id'])
				
				summary['summary'] = args['summary'] or summary['summary']

				phaseCount = 0
				
				for num, (cost, descr, date) in enumerate(zip(args['cost'], args['details'], args['date'])):
					phase = AgreementPhase.retrieveByAgreementIDAndPhaseNumber(agreement['id'], num)

					if not phase:
						phase = AgreementPhase(agreementID=agreement['id'], phaseNumber=num)
					
					if cost:
						phase['amount'] = cost
					
					if descr:
						phase['description'] = descr
					
					if date:
						phase['estDateCompleted'] = date
					
					unsavedRecords.append(phase)
					phaseCount += 1
				
				unsavedRecords.append(summary)
		
		# Clients can accept or decline an estimate, in which case the comment
		# fields in the agreement summary and agreement phase records get
		# updated; or they can dispute or verify a completed agreement, in
		# which case the dispute fields in the agreement summary and agreement
		# phase records get updated.

		elif role == "client":
			try:
				args = fmt.Parser(self.request.arguments,
					optional=[
						('summaryComments', fmt.Enforce(str)),
						('phaseComments', fmt.List(fmt.Enforce(str))),
					]
				)
			except fmt.HTTPErrorBetter as e:
				logging.warn(e.__dict__)
				self.set_status(e.status_code)
				self.write(e.body_content)
				return

			if isinstance(currentState, EstimateState) and action == 'decline':
				agreementSummary = AgreementSummary.retrieveByAgreementID(agreement['id'])

				if not agreementSummary:
					agreementSummary = AgreementSummary()
					agreementSummary['agreementID'] = agreement['id']
				
				agreementSummary['comments'] = args['summaryComments']
				agreementSummary.save()
				
				for phase in AgreementPhase.iteratorWithAgreementID(agreement['id']):
					if phase['phaseNumber'] < len(args['phaseComments']):
						phase['comments'] = args['phaseComments'][phase['phaseNumber']]
						phase.save()
			elif isinstance(currentState, CompletedState) and action == 'dispute':
				# phase = agreement.getCurrentPhase()
				currentPhase['comments'] = args['phaseComments'][0] # is vector for decline, scalar for dispute :(
				currentPhase.save()
		
		try:
			formerState = currentState
			currentState = currentState.performTransition(role, action, unsavedRecords, phase=currentPhase)
			
			# The new state is not used below this point, but the old one is. This
			# assignment is to make that clear until I clean this up [Bb]
			
			actionMap = {
				'send': 'agreementSent',
				'accept': 'agreementAccepted',
				'decline': 'agreementDeclined',
				'mark_complete': 'agreementWorkCompleted',
				'dispute': 'agreementDisputed'
			}
			
			if action in actionMap:
				recipient = User.retrieveByID(
					agreement['vendorID'] if role == 'client' else agreement['clientID']
				)
				
				msg = dict(agreementID=agreement['id'], action=actionMap[action])
				
				if role == 'vendor':
					recipient = User.retrieveByID(agreement['clientID'])
					clientState = recipient.getCurrentState()
					
					# For users that have not yet signed up on the platform,
					# create the necessary confirmation codes and perform a
					# user state transition. Override the 'agreementSent'
					# action to say 'agreementInvite'.
					
					# Only override if the agreement was just sent for the
					# first time.
					
					if isinstance(clientState, (
								PendingUserState, NewUserState, InvitedUserState, BetaUserState
							)) and isinstance(formerState, (DraftState, EstimateState)):
						# TODO: I think the transition could happen in the
						# notification daemon since the new state is never
						# referenced.
						
						clientState.performTransition("send_verification", {})
						msg['action'] = 'agreementInvite'
				else:
					recipient = User.retrieveByID(agreement['vendorID'])
				
				if action in ['mark_complete', 'dispute']:
					msg['agreementPhaseID'] = currentPhase['id']
				
				# The message's 'userID' field should really be called 'recipientID'
				msg['userID'] = recipient['id']
				
				with Beanstalk() as bconn:
					tube = self.application.configuration['notifications']['beanstalk_tube']
					bconn.use(tube)
					msgJSON = json.dumps(msg)
					r = bconn.put(msgJSON)
					logging.info('Beanstalk: %s#%d %s', tube, r, msgJSON)

			paymentMethod = PaymentBase.retrieveDefaultByUserID(user['id'])

			if action == 'mark_complete' and paymentMethod.tableName == 'zipmarkPaymentMethod':
				# We need to create a Zipmark bill here. We don't send it yet,
				# but a work queue assembles the bill and records its id and URL.
				
				userPayment = UserPayment.retrieveByPMIDAndPMTable(
					paymentMethod['id'], paymentMethod.tableName
				)

				msg = dict(
					action="createBill",
					vendorID=user['id'],
					agreementPhaseID=currentPhase['id'],
					userPaymentID=userPayment['id']
				)

				with Beanstalk() as bconn:
					tube = self.application.configuration['zipmark']['beanstalk_tube']
					bconn.use(tube)
					msgJSON = json.dumps(msg)
					r = bconn.put(msgJSON)
					logging.info('Beanstalk: %s#%d %s', tube, r, msgJSON)
					
		
		except StateTransitionError as e:
			errorMap = {
				'actionNotAllowed': {
					'domain': 'application.consistency',
					'display': (
						"The action you requested is not something you can do "
						"to this agreement."
					),
					'debug': "action not allowed",
					'status': 400
				},
				'unknownAction': {
					'domain': 'application.consistency',
					'display': (
						"This agreement doesn't support the action you requested. "
						"Please reload the page and try again."
					),
					'debug': "unknown action for current state",
					'status': 400
				},
				'missingClient': {
					'domain': 'application.consistency',
					'display': (
						"To send an estimate, you must specify a client. "
						"Please enter a recipient's name or email address."
					),
					'debug': "'clientID' value required to send estimate",
					'status': 400
				},
				'missingPhases': {
					'domain': 'application.conflict',
					'display': (
						"You must include at least one phase in order to "
						"send this agreement. Please provide a cost, "
						"estimated date of completion, and description "
						"for at least one phase of work."
					),
					'debug': "'cost', 'details', and 'date' parameters must not be empty",
					'status': 400
				},
				'default': {
					'domain': 'application.consistency',
					'display': (
						"We were unable to process your request at this time. "
						"Could you please try again in a moment? If the problem "
						"persists, you can get in touch with our support staff."
					),
					'debug': "error location (file marker / stacktrace ID)",
					'status': 400
				}
			}

			error = errorMap.get(e.type, None) or errorMap['default']
			status = error['status']
			del error['status']
			
			self.error_description = error
			raise web.HTTPError(status, e.message)

		for record in unsavedRecords:
			record.save()

		self.renderJSON(self.assembleDictionary(agreement))

