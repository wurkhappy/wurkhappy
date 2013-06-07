from models.user import User
from models.paymentmethod import UserPayment, PaymentBase, ZipmarkPaymentMethod
from models.agreement import Agreement, AgreementSummary, AgreementPhase
from models.transaction import Transaction, ZipmarkTransaction
from controllers.orm import ORMJSONEncoder
from controllers.data import Data, Base58
from controllers.zipmark import Zipmark

import json
import logging
import hashlib
import urllib

from uuid import uuid4
from datetime import datetime
import requests
from requests.auth import HTTPDigestAuth



class QueueHandler(object):
	def __init__(self, application):
		self.application = application
		self.config = application.config

	def createZipmarkBill(self, vendor, client, phase, userPayment):
		'''
		Given a client, vendor and agreement phase, create a Zipmark bill
		for the completed work.
		'''
		
		agreementSummary = AgreementSummary.retrieveByAgreementID(phase['agreementID'])
		paymentMethod = PaymentBase.retrieveByUserPaymentID(userPayment['id'])

		if not paymentMethod or paymentMethod.tableName != 'zipmarkPaymentMethod':
			raise Exception("vendor's payment method doesn't match our records")
		
		uniquingAgent = Data(uuid4().get_bytes()).stringWithEncoding(Base58)[:5]
		transactionDate = datetime.utcnow()

		transaction = Transaction(
			transactionReference='{0}.{1}'.format(phase['id'], uniquingAgent),
			agreementPhaseID=phase['id'],
			senderID=client['id'],
			recipientID=vendor['id'],
			userPaymentID=userPayment['id'],
			amount=phase['amount'],
			dateInitiated=transactionDate
		)
		transaction.save()

		templateData = {} # Data to populate the template goes here.
		
		host = self.config['zipmark'].get('api_host', '')
		resource = 'bills'
		ordinals = {
			1: 'First',
			2: 'Second',
			3: 'Third',
			4: 'Fourth',
			5: 'Fifth
		}

		bodyParams = {
			'bill' : {
				'bill_template_id': self.config['zipmark']['bill_template_id'],
				'identifier': transaction['transactionReference'],
				'date': '{0:%Y-%m-%d}'.format(transactionDate),
				'amount_cents': phase['amount'],
				'content': json.dumps(templateData),
				'memo': '{0} Payment for "{1}"'.format(
					ordinals[phase['phaseNumber'] + 1], agreementSummary['summary']
				)
			}
		}
		headers = {
			'Accept': 'application/vnd.com.zipmark.v2+json',
			'Content-Type': 'application/vnd.com.zipmark.v2+json'
		}

		r = requests.post('https://{0}/{1}'.format(host, resource), # baseURL + 'bills', 
			data=json.dumps(bodyParams),
			headers=headers,
			auth=HTTPDigestAuth(paymentMethod['vendorID'], paymentMethod['vendorSecret'])
		)

		if r.status_code == 201:
			# Bill created; handle the response.
			billResponse = r.json()
			billURL = None

			for link in billResponse['bill']['links']:
				if link['rel'] == 'web':
					billURL = link['href']
					break

			# Get data from bill
			bill = ZipmarkTransaction(
				transactionID=transaction['id'],
				zipmarkBillID=billResponse['bill']['id'],
				zipmarkBillURL=billURL
			)

			return bill
		else:
			logging.error(json.dumps({
				'message': 'Unexpected response from Zipmark',
				'response': {
					'status': r.status_code,
					'body': r.text
				}
			}))
		# else:
		# 	logging.error(json.dumps({
		# 		'message': 'Zipmark bill creation failed',
		# 		'exception': str(e)
		# 	}))

		return None



class TestHandler(QueueHandler):
	def receive(self, body):
		logging.info('{"message": "received message"}')
		user = User.retrieveByID(body['userID'])
		
		if user:
			logging.info(json.dumps({
				"message": "Zipmark signup test hook received user",
				"userID": user['id']
			}))
		else:
			raise Exception("no such user")



class SignupHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])

		if not user:
			raise Exception("no such user")
		
		filename = self.config['zipmarkd'].get('signup_file', 'user_signups.txt')
		userString = "{0} -- {1} ({2})\n".format(user['id'], user.getFullName(), user['email'])

		with open(filename, 'a') as f:
			f.write(userString)

		paymentMethod = ZipmarkPaymentMethod()
		paymentMethod.save()

		userPayment = UserPayment(
			userID=user['id'],
			pmID=paymentMethod['id'],
			pmTable=paymentMethod.tableName
		)
		userPayment.save()

		# Enqueue verification status onto the Nginx HTTP push module.
		# This is a temporary hack, and should probably use a unique ID
		# that's not the user's UID.
		
		host = self.config['zipmarkd'].get('http_push_host', '127.0.0.1')
		prefix = self.config['zipmarkd'].get('http_push_host', '')

		notificationResponse = requests.post('http://{0}/?chan={1}&id={2}'.format(host, prefix, user['id']),
			headers={'Content-Type': 'application/json'},
			data=json.dumps({'userID': user['id'], 'zipmarkSignupRegistered': True})
		)
		
		if notificationResponse.status_code in [200, 201]:
			logging.info(json.dumps({
				"message": "Zipmark signup appended info for user",
				"userID": user['id'],
				"signupString": userString
			}))
		else:
			logging.error(json.dumps({
				'message': 'Publishing to Nginx HTTP push queue failed',
				'exception': 'I don\'t know'
			}))
		



class CreateBillHandler(QueueHandler):
	def receive(self, body):
		vendor = User.retrieveByID(body['vendorID'])

		if not vendor:
			raise Exception("no such user for vendorID")
		
		currentPhase = AgreementPhase.retrieveByID(body['agreementPhaseID'])

		if not currentPhase:
			raise Exception("no such phase")

		agreement = Agreement.retrieveByID(currentPhase['agreementID'])

		if agreement['vendorID'] != vendor['id']:
			raise Exception("vendor's ID does not match agreement's vendor ID")
		
		userPayment = UserPayment.retrieveByID(body['userPaymentID'])
		
		if not userPayment:
			raise Exception("no such payment record for specified user")

		client = User.retrieveByID(agreement['clientID'])

		bill = self.createZipmarkBill(client, vendor, currentPhase, userPayment)

		if bill:
			bill.save()
		else:
			raise Exception("unable to create Zipmark bill")

		logging.info(json.dumps({
			"message": "Created Zipmark bill for user",
			"clientID": client['id'],
			"vendorID": vendor['id'],
			"billID": bill['id']
		}))

