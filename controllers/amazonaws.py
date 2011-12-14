from boto.s3.connection import S3Connection

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