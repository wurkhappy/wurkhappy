from __future__ import division

from base import *
from models.user import User, UserPrefs, ActiveUserState
from models.transaction import Transaction
from controllers import fmt
from controllers.amazonaws import AmazonFPS

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
			self.verifySignature('{0}://{1}{2}'.format(
					self.request.protocol,
					self.application.configuration['wurkhappy']['hostname'],
					self.request.path
				),
				self.request.arguments,
				self.application.configuration['amazonaws']
			)
			
			transaction = Transaction.retrieveByTransactionReference(args['referenceId'])
		
			if transaction is None:
				amtParser = re.compile('USD ([0-9]+(?:\.[0-9]{0,2})?)')
				amountString = amtParser.match(args['transactionAmount']).groups()[0]
			
				transaction = Transaction(
					transactionReference=args['referenceId'],
					amount=int(float(amountString) * 100),
					dateInitiated=datetime.fromtimestamp(args['transactionDate'])
				)
		
		if args['status'] == 'PS':
			transaction['dateApproved'] = datetime.now()
		elif args['status'] in ['ME', 'PF', 'SE']:
			transaction['dateDeclined'] = datetime.now()
		
		transaction.save()
		
		self.renderJSON(["OK"])
		return