from __future__ import division

from base import *
from models.user import User, UserPrefs, UserDwolla
from models.agreement import Agreement, CompletedState, StateTransitionError
from models.paymentmethod import PaymentMethod
from models.transaction import Transaction
from controllers.beanstalk import Beanstalk
from controllers import fmt

from tornado.httpclient import HTTPClient, HTTPError
from tornado.curl_httpclient import CurlAsyncHTTPClient

from datetime import datetime

import urllib
import json
import logging
import os



# -------------------------------------------------------------------
# PaymentHandler
# -------------------------------------------------------------------

class PaymentHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	@web.asynchronous
	def post(self):
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('password', fmt.Enforce(str)),
					('agreementID', fmt.Enforce(int)),
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			self.finish()
			return
		
		if not user: # (user and user.passwordIsValid(args['password'])):
			# User wasn't found, or password is wrong, display error
			# @todo: Exponential back-off when user enters incorrect password.
			# @todo: Flag accounds if incorrect password is presented too often.
			error = {
				"domain": "web.request",
				"debug": "please validate authentication credentials",
				"display": (
					"The password you entered does not match the one we have "
					"on record. Did you mistype? Is caps lock turned off?\n\n"
					"If you've forgotten your password, you can reset it "
					"by clicking the 'Reset Password' link in the Password "
					"tab of the Accounts page."
				)
			}
			self.set_status(401)
			self.renderJSON(error)
			self.finish()
			return
		
		agreement = Agreement.retrieveByID(args['agreementID'])
		phase = agreement.getCurrentPhase()
		
		if not phase:
			error = {
				"domain": "web.request",
				"debug": "no such phase"
			}
			self.set_status(404)
			self.renderJSON(error)
			self.finish()
			return
		
		# agreement = Agreement.retrieveByID(phase.agreementID)
		
		if not (agreement and agreement['clientID'] == user['id']):
			# The logged-in user is not authorized to make a payment
			# on this agreement. I don't know how it's even possible
			# to get to this point.
			error = {
				"domain": "application.not_authorized",
				"debug": "I'm sorry Dave, I can't do that"
			}
			self.set_status(403)
			self.renderJSON(error)
			self.finish()
			return
		
		agreementState = agreement.getCurrentState()
		
		if not isinstance(agreementState, CompletedState):
			error = {
				"domain": "application.consistency",
				"display": "The request could not be completed at this time. :(((",
				"debug": "tried to pay an incomplete phase"
			}
			
			self.set_status(409)
			self.renderJSON(error)
			self.finish()
			return
		
		# Look up the user's preferred payment method
		
		# paymentPref = UserPrefs.retrieveByUserIDAndName(user['id'], 'preferredPaymentID')
		# 
		# if paymentPref:
		# 	paymentMethod = PaymentMethod.retrieveByID(paymentPref['value'])
		# else:
		# 	paymentMethod = PaymentMethod.retrieveACHMethodWithUserID(user['id'])
		# 	
		# 	if not paymentMethod:
		# 		paymentMethod = PaymentMethod.retrieveCCMethodWithUserID(user['id'])
		# 
		# if not paymentMethod:
		# 	error = {
		# 		'domain': 'application.not_found',
		# 		'display': (
		# 			"There's no payment method on file. Please add bank "
		# 			"account or credit card information to continue."
		# 		),
		# 		'debug': 'no payment method on file'
		# 	}
		# 	self.set_status(400)
		# 	self.renderJSON(error)
		# 	return
		
		# For now, we look for a Dwolla account for the user.
		
		# @TODO: LOOK FOR DWOLLA ACCOUNT
		
		transaction = Transaction.retrieveByAgreementPhaseID(phase['id'])
		
		if not transaction:
			transaction = Transaction()
			transaction['agreementPhaseID'] = phase['id']
			transaction['senderID'] = user['id']
			transaction['recipientID'] = agreement['vendorID']
			# transaction['paymentMethodID'] = paymentMethod['id']
			transaction['amount'] = phase['amount']
			transaction.save()
		
		# transactionMsg = dict(
		# 	action='transactionSubmitPayment',
		# 	senderID=transaction['senderID'],
		# 	recipientID=transaction['recipientID'],
		# 	agreementPhaseID=phase['id'],
		# 	pin=args['password']
		# )
		# 
		# with Beanstalk() as bconn:
		# 	tube = self.application.configuration['transactions']['beanstalk_tube']
		# 	bconn.use(tube)
		# 	msgJSON = json.dumps(transactionMsg)
		# 	r = bconn.put(msgJSON)
		# 	logging.info('Beanstalk: %s#%d %s', tube, r, msgJSON)
		
		self.agreement = agreement
		self.transaction = transaction
		self.agreementState = agreementState
		
		sender = UserDwolla.retrieveByUserID(user['id'])
		recipient = UserDwolla.retrieveByUserID(agreement['vendorID'])
		
		if not (sender and recipient):
			error = {
				"domain": "application.consistency",
				"display": (
					"One of the parties to the transaction does not have a "
					"Dwolla account. This error should not be able to happen."
				),
				"debug": "one or more parties is missing a Dwolla account"
			}
			
			self.set_status(400)
			self.renderJSON(error)
			self.finish()
			return
			
		
		baseURL = 'https://www.dwolla.com/oauth/rest/transactions/send'
		queryArgs = {
			'oauth_token': sender['oauthToken']
		}
		bodyArgs = {
			'pin': args['password'],
			'destinationId': recipient['dwollaID'],
			'amount': "{:.2f}".format(phase['amount'] / 100),
		}

		queryString = '&'.join('{0}={1}'.format(key, urllib.quote(val, '/')) for key, val in queryArgs.iteritems())
		logging.info('requestURL: ' + baseURL + '?' + queryString)
		logging.info(bodyArgs)
		
		c = CurlAsyncHTTPClient()
		c.fetch(baseURL + '?' + queryString,
			method="POST",
			headers={'Content-Type': 'application/json'},
			body=json.dumps(bodyArgs),
			callback=self._dwollaResponseHandler
		)
	
	
	def _dwollaResponseHandler(self, response):
		if isinstance(response, HTTPError):
			logging.error('Dwolla transaction error: %s', response)
			self.set_status(400)
			self.renderJSON(error)
			self.finish()
			return
		
		body = json.loads(response.body)
		
		if body['Success'] == False:
			error = {
				"domain": 'external.dwolla',
				"display": "There was an error processing your transaction.",
				"debug": 'Dwolla transaction error: {0}'.format(body['Message'])
			}
			
			if body['Message'] == 'Invalid account PIN':
				error['display'] = (
					"The PIN you entered did not match the one Dwolla has on "
					"record for your account."
				)
			elif body['Message'] == 'Insufficient funds.':
				error['display'] = (
					"You do not have enough funds in your Dwolla account to "
					"make this transaction. Please transfer funds into your "
					"account and try again."
				)
			elif body['Message'] == 'Account temporarily locked':
				error['display'] = (
					"Your Dwolla account has been temporarily locked. This is "
					"probably due to too many incorrect PIN entries in a row. "
					"Your account will automatically unlock after 30 minutes."
				)
				error['final'] = True
			
			
			self.transaction['dateDeclined'] = datetime.now()
			self.transaction.save()
			
			self.set_status(400)
			self.renderJSON(error)
			self.finish()
			return
		
		logging.info(response)
		unsavedRecords = []
		
		try:
			self.agreementState.performTransition('client', 'verify', unsavedRecords)
		except StateTransitionError as e:
			error = {
				"domain": "application.consistency",
				"display": (
					"We were unable to process your request at this time. "
					"Could you please try again in a moment? If the problem "
					"persists, please contact our support team."
				),
				"debug": "error location (file marker / stacktrace ID)"
			}
			
			self.transaction['dateDeclined'] = datetime.now()
			self.transaction.save()
			
			self.set_status(409)
			self.renderJSON(error)
			self.finish()
			return
		
		# The message's 'userID' field should really be called 'recipientID'
		msg = dict(
			agreementID=self.agreement['id'],
			transactionID=self.transaction['id'],
			userID=self.agreement['vendorID'],
			action='agreementPaid'
		)
		
		with Beanstalk() as bconn:
			tube = self.application.configuration['notifications']['beanstalk_tube']
			bconn.use(tube)
			msgJSON = json.dumps(msg)
			r = bconn.put(msgJSON)
			logging.info('Beanstalk: %s#%d %s', tube, r, msgJSON)
		
		for record in unsavedRecords:
			record.save()
		
		self.transaction['dateApproved'] = datetime.now()
		self.transaction['dwollaTransactionID'] = body['Response']
		self.transaction.save()
		
		transactionJSON = self.transaction.publicDict()
		del(transactionJSON['paymentMethodID'])
		
		self.renderJSON(transactionJSON)
		self.finish()

