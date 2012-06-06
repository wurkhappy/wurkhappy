from controllers.data import Data, Base64

from boto.s3.connection import S3Connection
from collections import OrderedDict
from hashlib import sha1
import hmac
import urllib



class AmazonAWSConnectionError(Exception):
	pass



class AmazonS3(object):
	settings = {}
	
	@classmethod
	def configure(clz, settings, tag=None):
		clz.settings[tag] = settings
	
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
	
	def generateSignature(self, httpVerb, host, uri, data, key):
		'''Generate an Amazon FPS signature for an API request or button form.
		More information can be found at the following URL:
		http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/Sig2CreateSignature.html
		'''

		canonicalData = OrderedDict()

		for k in sorted(data.keys()):
			canonicalData[urllib.quote(k, '~')] = urllib.quote(data[k], '~')

		canonicalString = '&'.join('{0}={1}'.format(k, v) for k, v in canonicalData.iteritems())

		plaintext = '{0}\n{1}\n{2}\n{3}'.format(
			httpVerb,
			host.lower(),
			'/{0}'.format(uri),
			canonicalString
		)

		hashObj = hmac.new(key, plaintext, sha1)
		data = Data(hashObj.digest())
		return data.stringWithEncoding(Base64)
	
	def verifySignature(self):
		'''This is obviously not right.'''
		return True
