from controllers.data import Data, Base64
from tornado.httpclient import HTTPClient, HTTPError

from elementtree import ElementTree as ET
from boto.s3.connection import S3Connection
from collections import OrderedDict
from hashlib import sha256
from datetime import datetime
import hmac
import urllib
import logging


class AmazonAWSConnectionError(Exception):
	pass



class AmazonS3(object):
	settings = {}
	
	@classmethod
	def configure(clz, settings, tag=None):
		clz.settings[tag] = settings
	
	@classmethod
	def getSettingWithTag(clz, name, tag=None):
		return clz.settings.get(tag, {}).get(name, None)
	
	def __init__(self, tag=None):
		self._tag = tag if tag in self.settings else None
	
	def __enter__(self):
		if self._tag not in self.settings:
			raise AmazonAWSConnectionError('amazon aws not configured')
		
		# Set up Boto objects: connect to S3 and create bucket object
		self._conn = S3Connection(self.settings[self._tag]['key_id'], self.settings[self._tag]['key_secret'])
		self._bucket = self._conn.create_bucket(self.settings[self._tag]['bucket_name'])
		return (self._conn, self._bucket)
	
	def __exit__(self, type, value, traceback):
		# Be a good guest and clean up after yourself. Just realized this is *soooo* not threadsafe.
		#self._conn.close()
		pass



class AmazonFPS(object):
	'''Helper method mix-in for Amazon Payments'''
	
	variableMarketplaceFee = 5.0

	def generateSignature(self, httpVerb, host, uri, data):
		'''Generate an Amazon FPS signature for an API request or button form.
		More information can be found at the following URL:
		http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/Sig2CreateSignature.html
		'''

		key = AmazonS3.getSettingWithTag('key_secret')
		canonicalData = OrderedDict()

		for k in sorted(data.keys()):
			if k != 'Signature':
				canonicalData[urllib.quote(k, '~')] = urllib.quote(data[k], '~')

		canonicalString = '&'.join('{0}={1}'.format(k, v) for k, v in canonicalData.iteritems())
		
		plaintext = '{0}\n{1}\n{2}\n{3}'.format(
			httpVerb.upper(),
			host.lower(),
			'/{0}'.format(uri),
			canonicalString
		)
		
		return Data(hmac.new(key, plaintext, sha256).digest()).stringWithEncoding(Base64)
	
	def verifySignature(self, requestURL, httpParams, amazonSettings):
		'''Verifies the signature of an Amazon FPS callback or IPN notification
		by making a signed API request to the verification endpoint of the
		Amazon FPS API.'''
		
		baseURL = 'https://{0}/'.format(AmazonS3.getSettingWithTag('fps_host'))
		queryArgs = {
			'Action': 'VerifySignature',
			'AWSAccessKeyId': AmazonS3.getSettingWithTag('key_id'),
			'UrlEndPoint': requestURL,
			'HttpParameters': httpParams, # '&'.join('{0}={1}'.format(key, val) for key, val in httpParams.iteritems()),
			'SignatureVersion': '2',
			'SignatureMethod': 'HmacSHA256',
			'Timestamp': datetime.utcnow().isoformat() + 'Z', # Fuck you, Python!
			'Version': '2008-09-17'
		}
		
		queryArgs['Signature'] = self.generateSignature('GET', AmazonS3.getSettingWithTag('fps_host'), '', queryArgs)
		
		queryString = '&'.join('{0}={1}'.format(key, urllib.quote(val, '~')) for key, val in queryArgs.iteritems())
		logging.info('Verify Signature URL: %s', baseURL + '?' + queryString)
		
		httpClient = HTTPClient()
		
		try:
			exchangeResponse = httpClient.fetch(baseURL + '?' + queryString)
		except HTTPError as e:
			logging.error('Amazon FPS signature validation failed: %s', e)
		else:
			try:
				xml = ET.XML(exchangeResponse.body)
			except SyntaxError as e:
				logging.error('Amazon FPS signature validation response did not contain valid XML: %s', e)
			else:
				xmlns = '{http://fps.amazonaws.com/doc/2008-09-17/}'
				success = xml.findtext('{0}VerifySignatureResult/{0}VerificationStatus/'.format(xmlns))
				return success == 'Success'
		
		return False

