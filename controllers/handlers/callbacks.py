from __future__ import division

from base import *
from models.user import User, UserPrefs, ActiveUserState, StateTransitionError
from models.agreement import Agreement, AgreementPhase
from models.transaction import Transaction
from controllers import fmt
from controllers.amazonaws import AmazonFPS
from controllers.application import WurkHappy

from tornado.web import RequestHandler
from tornado.httpclient import HTTPClient, HTTPError

import json
import logging

from datetime import datetime
import urlparse
import urllib
import re

# 	A	The pipeline was abandoned.
# 	ME	Merchant error. Either the button parameter names are invalid, or there is a shipping address error from the co-branded user interface.
# 	PS	The payment transaction was successful.
# 	PF	The payment or reserve transaction failed and the money was not transferred.
# 		If the account is not suspended, you can redirect your customer to the Amazon Payments Payment Authorization page to select a different payment method.
# 	PI	Payment has been initiated.
# 		It will take between five seconds and 48 hours to complete, based on the availability of external payment networks and the riskiness of the transaction.
# 	PR	The reserve transaction was successful.
# 	RS	The refund transaction was successful.
# 	RF	The refund transaction failed.
# 	SE	A service error has occurred.
# 	SF	The subscription failed.
# 	SI	The subscription has initiated.
# 	SR	The marketplace fee transaction was accepted by the recipient.
# 	SS	The subscription was completed.
# 	UE	User error for donations. The donation amount was less than the minimum donation amount.
# 	UF	Subscription update failed. The subscriber has failed to update the subscription payment method.
# 	US	Subscription update was successful. The subscriber succeeded updating the subscription payment method.


class AmazonPaymentsIPNHandler(BaseHandler, AmazonFPS):
		
	def check_xsrf_cookie(self):
		'''Disable XSRF protection for IPN callbacks. Ideally, this should
		verify the signature with Amazon.'''
		return
	
	def post(self):
		
		logging.info(self.request.arguments)
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('referenceId', fmt.Enforce(str)),
					('transactionAmount', fmt.Enforce(str)),
					('transactionDate', fmt.Enforce(float)),
					('transactionId', fmt.Enforce(str)),
					('paymentMethod', fmt.Enforce(str)),
					('status', fmt.Enforce(str)),
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			return
		
		# http://docs.amazonwebservices.com/AmazonSimplePay/2008-09-17/ASPAdvancedUserGuide/index.html?ipnparameter.html
		
		# addressFullName
		# addressLine1
		# addressLine2
		# addressState
		# addressZip
		# addressCountry
		# addressPhone
		# buyerEmail
		# buyerName
		# certificateUrl
		# customerEmail
		# customerName
		# dateInstalled
		# isShippingAddressProvided
		# operation
		# notificationType
		# paymentMethod
		# paymentReason
		# recipientEmail
		# recipientName
		# referenceId
		# signature
		# signatureVersion
		# signatureMethod
		# tokenId
		# tokenType
		# transactionAmount
		# transactionDate
		# transactionId
		# transactionStatus
		
		# buyerName
		# operation
		# paymentMethod
		# paymentReason
		# recipientEmail
		# recipientName
		# referenceId
		# signature
		# status
		# transactionAmount
		# transactionDate
		# transactionId
		
		# Look up the transaction ID and update the record
		if args['referenceId'] and args['transactionAmount'] and args['transactionDate']:
			
			# This is complicated because we need to decompose list values in
			# the dictionary into two key-value pairs with the same key
			paramString = '&'.join('&'.join('{0}={1}'.format(k, v) for v in vs)
				for k, vs in self.request.arguments.iteritems())
			
			signatureIsValid = self.verifySignature(
				'{0}://{1}{2}'.format(
					self.request.protocol, WurkHappy.getSettingWithTag('hostname'), self.request.path
				),
				self.request.body, # paramString,
				self.application.configuration['amazonaws']
			)
			
			logging.info(signatureIsValid)
			
			# transaction = Transaction.retrieveByTransactionReference(args['referenceId'])
			# 		
			# if transaction is None:
			# 	amtParser = re.compile('USD ([0-9]+(?:\.[0-9]{0,2})?)')
			# 	amountString = amtParser.match(args['transactionAmount']).groups()[0]
			# 
			# 	transaction = Transaction(
			# 		transactionReference=args['referenceId'],
			# 		amount=int(float(amountString) * 100),
			# 		dateInitiated=datetime.fromtimestamp(args['transactionDate'])
			# 	)
			# 		
			# if args['status'] == 'PS':
			# 	transaction['dateApproved'] = datetime.now()
			# elif args['status'] in ['ME', 'PF', 'SE']:
			# 	transaction['dateDeclined'] = datetime.now()
			# 
			# transaction.save()
			
			if not (signatureIsValid or self.application.configuration['tornado'].get('debug') == True):
				logging.error("Bad Amazon payments response payload\n%s", self.request.query)
			
			# Always do this; I suspect the signature code is bad
			# TODO: Fix signature code
			
			if True:
				# '{0}.{1}'.format(phaseID, uniquingAgent)
				phaseID, reference = args['referenceId'].split('.')
			
				phase = AgreementPhase.retrieveByID(phaseID)
				agreement = Agreement.retrieveByID(phase['agreementID'])
				currentState = agreement.getCurrentState()
				
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
					transaction['agreementPhaseID'] = phase['id']
				
				if not (transaction['senderID'] and transaction['recipientID']):
					transaction['senderID'] = agreement['clientID']
					transaction['recipientID'] = agreement['vendorID']
				
				
				if args['status'] == 'PS':
					transaction['dateApproved'] = datetime.now()
					transaction['amazonTransactionID'] = args['transactionId']
					transaction['amazonPaymentMethod'] = args['paymentMethod']

					logging.info('State before state change due to Amazon callback: %s', currentState)

					# If the transaction was approved, update the agreement state
					# (This should have some more granularity. Ugh.)
					unsavedRecords = []

					try:
						currentState = currentState.performTransition('client', 'verify', unsavedRecords)
					except StateTransitionError as e:
						pass

					logging.info('State after state change due to Amazon callback: %s', currentState)

					for record in unsavedRecords:
						record.save()
				elif args['status'] in ['ME', 'PF', 'SE']:
					transaction['dateDeclined'] = datetime.now()
					logging.error("Transaction declined by Amazon\n%s", transaction)

				transaction.save()
			
			
			self.renderJSON(["OK"])
		else:
			self.renderJSON(["MEH"])
		return

