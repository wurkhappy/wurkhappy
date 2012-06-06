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