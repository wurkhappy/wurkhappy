from models.user import User
from models.transaction import Transaction
from models.paymentmethod import AmazonPaymentMethod
from controllers.orm import ORMJSONEncoder
from controllers.amazonaws import AmazonFPS, AmazonS3

import tornado.template as template
import json
import logging
import hashlib
import urllib

from datetime import datetime
from tornado.httpclient import HTTPClient, HTTPError
from elementtree import ElementTree as ET


class QueueHandler(object):
	def __init__(self, application):
		self.application = application
		self.config = application.config
	
	def getAmazonAccountStatus(self, amazonToken):
		"""
		Given an Amazon Payments Token ID, make an Amazon FPS API call and
		return the account verification status.
		
		http://docs.amazonwebservices.com/AmazonFPS/latest/FPSAdvancedGuide
		/GetRecipientVerificationStatus.html
		
		Responses from the Amazon FPS API are:
		- "VerificationPending"
		- "VerificationComplete"
		- "VerificationCompleteNoLimits"
		
		:param amazonToken: the user's Amazon Payments account token ID
		:returns: account verification status
		:rtype: string or None
		
		"""
		
		# TODO: This should probably all go into an AmazonFPS class...
		
		fps = AmazonFPS()
		
		baseURL = 'https://{0}/'.format(AmazonS3.getSettingWithTag('fps_host'))
		queryArgs = {
			'Action': 'GetRecipientVerificationStatus',
			'AWSAccessKeyId': AmazonS3.getSettingWithTag('key_id'),
			'RecipientTokenId': amazonToken,
			'SignatureVersion': '2',
			'SignatureMethod': 'HmacSHA256',
			'Timestamp': datetime.utcnow().isoformat() + 'Z', # Fuck you, Python!
			'Version': '2008-09-17'
		}
		
		queryArgs['Signature'] = fps.generateSignature('GET', AmazonS3.getSettingWithTag('fps_host'), '', queryArgs)
		
		queryString = '&'.join('{0}={1}'.format(key, urllib.quote(val, '~')) for key, val in queryArgs.iteritems())
		
		logging.info(json.dumps({
			'message': 'Geting verification status for user',
			'requestURL': '{0}?{1}'.format(baseURL, queryString)
		}))
		
		httpClient = HTTPClient()
		
		try:
			accountStatusResponse = httpClient.fetch(baseURL + '?' + queryString)
		except HTTPError as e:
			logging.error(json.dumps({
				'message': 'Amazon FPS signature validation failed',
				'exception': str(e)
			}))
		else:
			if accountStatusResponse.code == 200:
				try:
					xml = ET.XML(accountStatusResponse.body)
				except SyntaxError as e:
					logging.error(json.dumps({
						'message': 'Amazon FPS signature validation response did not contain valid XML',
						'exception': str(e)
					}))
				else:
					xmlns = '{http://fps.amazonaws.com/doc/2008-09-17/}'
					success = xml.findtext('{0}GetRecipientVerificationStatusResult/{0}RecipientVerificationStatus/'.format(xmlns))
					return success
			else:
				logging.error(json.dumps({
					'message': 'Unexpected response from Amazon FPS',
					'response': {
						'status': accountStatusResponse.code,
						'bdoy': accountStatusResponse.body
					}
				}))
		
		return None



class TestHandler(QueueHandler):
	def receive(self, body):
		logging.info('{"message": "received message"}')
		user = User.retrieveByID(body['userID'])
		paymentMethod = AmazonPaymentMethod.retrieveByUserID(user['id'])

		if user:
			if not (paymentMethod['recipientEmail'] and paymentMethod['tokenID']):
				raise Exception("User has not Accepted Amazon's marketplace terms")
			
			logging.info(json.dumps({
				"message": "Amazon verification test hook recieved user",
				"userID": user['id'],
				"amazonPaymentsAccount": {
					"recipientEmail": paymentMethod['recipientEmail'],
					"tokenID": paymentMethod['tokenID']
				},
			}))
		else:
			raise Exception("No such user")



class VerificationHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])
		
		if not user:
			raise Exception("No such user")
		
		paymentMethod = AmazonPaymentMethod.retrieveByUserID(user['id'])

		if not (paymentMethod['recipientEmail'] and paymentMethod['tokenID']):
			raise Exception("User has not Accepted Amazon's marketplace terms")
		
		status = self.getAmazonAccountStatus(paymentMethod['tokenID'])
		
		if not status:
			raise Exception("Amazon API error")
		
		if status in ['VerificationComplete', 'VerificationCompleteNoLimits']:
			paymentMethod['verificationComplete'] = 1
			paymentMethod.save()

			# Enqueue verification status onto the Nginx HTTP push module.
			# This is a temporary hack, and should probably use a unique ID
			# that's not the user's UID.
			
			httpClient = HTTPClient()
			
			try:
				notificationResponse = httpClient.fetch('http://{0}/?chan={1}&id={2}'.format(
						self.config['amazond'].get('http_push_host', '127.0.0.1'),
						self.config['amazond'].get('http_push_prefix', ''),
						user['id']
					),
					method='POST',
					headers={'Content-Type': 'application/json'},
					body=json.dumps({
						'userID': user['id'],
						'amazonVerificationComplete': True
					})
				)
			except HTTPError as e:
				logging.error(json.dumps({
					'message': 'Publishing to Nginx HTTP push queue failed',
					'exception': str(e)
				}))
			
		
		logging.info(json.dumps({
			"message": "processed verification request",
			"userID": user['id'],
			"amazonPaymentsAccount": {
				"recipientEmail": amazonEmail['value'],
				"tokenID": amazonToken['value'],
				"verificationComplete": status in ['VerificationComplete', 'VerificationCompleteNoLimits']
			}
		}))

