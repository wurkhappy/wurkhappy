from models.user import User, UserPrefs
from models.transaction import Transaction
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
		amazonEmail = UserPrefs.retrieveByUserIDAndName(user['id'], 'amazon_recipient_email')
		amazonToken = UserPrefs.retrieveByUserIDAndName(user['id'], 'amazon_token_id')

		if user:
			if not (amazonEmail and amazonToken):
				raise Exception("User has not Accepted Amazon's marketplace terms")
			
			logging.info(json.dumps({
				"message": "Amazon verification test hook recieved user",
				"userID": user['id'],
				"amazonPaymentsAccount": {
					"recipientEmail": amazonEmail['value'],
					"tokenID": amazonToken['value']
				},
			}))
		else:
			raise Exception("No such user")



class VerificationHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])
		
		if not user:
			raise Exception("No such user")
		
		amazonEmail = UserPrefs.retrieveByUserIDAndName(user['id'], 'amazon_recipient_email')
		amazonToken = UserPrefs.retrieveByUserIDAndName(user['id'], 'amazon_token_id')
		
		if not (amazonEmail and amazonToken):
			raise Exception("User has not Accepted Amazon's marketplace terms")
		
		status = self.getAmazonAccountStatus(amazonToken['value'])
		
		if not status:
			raise Exception("Amazon API error")
		
		if status in ['VerificationComplete', 'VerificationCompleteNoLimits']:
			amazonConfirmed = UserPrefs.retrieveByUserIDAndName(user['id'], 'amazon_verification_complete')
			
			if not amazonConfirmed:
				amazonConfirmed = UserPrefs(
					userID=user['id'],
					name='amazon_verification_complete',
				)
			
			amazonConfirmed['value'] = 'True'
			amazonConfirmed.save()
			
			# Enqueue verification status onto the Nginx HTTP push module.
			# This is a temporary hack, and should probably use a unique ID
			# that's not the user's UID.
			
			httpClient = HTTPClient()
			
			try:
				notificationResponse = httpClient.fetch('http://127.0.0.1:1138/?id={0}'.format(user['id']),
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
