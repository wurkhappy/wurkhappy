from models.user import User, UserState, UserDwolla
from models.agreement import AgreementPhase
from models.transaction import Transaction
from controllers.orm import ORMJSONEncoder
from tornado.httpclient import HTTPClient, HTTPError
from tornado.curl_httpclient import CurlAsyncHTTPClient

from datetime import datetime
import json
import urllib
import logging



# 'transactionTest': transactions.TestHandler,
# 'transactionSubmitPayment': transactions.SubmitPaymentHandler

class QueueHandler(object):
	def __init__(self, application):
		self.application = application
	
	def submitPayment(self, sender, recipient, phase, pin):
		'''
		QueueHandler.submitPayment takes sender and recipient user objects and
		an agreement phase and submits an HTTP request to the Dwolla API.
		'''
		
		c = self.application.connection
		response = None
		
		baseURL = 'https://www.dwolla.com/oauth/rest/transactions/send'
		queryArgs = {
			'oauth_token': sender['oauthToken']
		}
		bodyArgs = {
			'pin': pin,
			'destinationId': recipient['dwollaID'],
			'amount': "{:.2f}".format(phase['amount']),
		}
		
		queryString = '&'.join('{0}={1}'.format(key, urllib.quote(val, '/')) for key, val in queryArgs.iteritems())
		logging.info('{"requestURL": "' + baseURL + '?' + queryString + '"}')
		
		try:
			response = c.fetch(baseURL + '?' + queryString,
				method="POST",
				headers={'Content-Type': 'application/json'},
				body=json.dumps(bodyArgs)
			)
		except HTTPError as e:
			logging.error('{{"error": "Dwolla transaction error: {0}"}}'.format(e))
		else:
			# We don't trust third parties, so, like, log the entire response
			logging.info('{{"http_status": {0}}}'.format(response.code))
			# The body is already JSON, so we don't need to quote it.
			logging.info('{{"http_response": {0}}}'.format(response.body))
			
			responseDict = None
			
			if response.code == 200:
				# Parse the response body and store the access token
				responseDict = json.loads(response.body)
			
			return responseDict



class TestHandler(QueueHandler):
	def receive(self, body):
		logging.info('{"message": "received message"}')
		sender = User.retrieveByID(body['senderID'])
		recipient = User.retrieveByID(body['recipientID'])
		phase = AgreementPhase.retrieveByID(body['agreementPhaseID'])
		
		if sender and recipient:
			logging.info(json.dumps({
				"message": "Transaction test hook recieved user",
				"actionType": body['action'],
				"senderID": sender['id'],
				"recipientID": recipient['id'],
				"agreementPhaseID": phase['id'],
			}))
		else:
			raise Exception("No such users")



class SubmitPaymentHandler(QueueHandler):
	def receive(self, body):
		sender = User.retrieveByID(body['senderID'])
		recipient = User.retrieveByID(body['recipientID'])
		phase = AgreementPhase.retrieveByID(body['agreementPhaseID'])
		
		if not phase:
			raise Exception("No such phase")
		
		if not sender or not recipient:
			raise Exception("No such users")
		
		senderDwolla = UserDwolla.retrieveByUserID(sender['id'])
		recipientDwolla = UserDwolla.retrieveByUserID(recipient['id'])
		
		response = None
		
		if senderDwolla and recipientDwolla:
			response = self.submitPayment(senderDwolla, recipientDwolla, phase, body['pin'])
		else:
			raise Exception("Sender or recipient is missing a Dwolla account")
		
		if response:
			transaction = Transaction.retrieveByAgreementPhaseID(phase['id'])
			
			if not transaction:
				raise Exception("No such transaction")
			
			if response['Success'] == False:
				logging.warn('{{"error": "Dwolla request error: {0}"}}'.format(response['Message']))
				transaction['dateDeclined'] = datetime.now()
			else:
				transaction['dateApproved'] = datetime.now()
				# transaction['dwollaTransactionID'] = response['Response']
			
			transaction.save()
