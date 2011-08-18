import boto

class AmazonS3(object):
	settings = {}
	
	@classmethod
	def configure(clz, settings, tag=None):
		clz.settings[tag] = settings
	
	def __init__(self, tag=None):
		self._tag = tag if tag in self.settings else None
	
	def __enter__(self):
		# do boto setup
		pass
	
	def __exit__(self):
		# do boto cleanup
		pass


	# def __enter__(self):
	# 	if self._mode not in self.settings:
	# 		raise DatabaseConnectionError('database not configured')
	# 	self._conn = MySQLdb.connect(**self.settings[self._mode])
	# 	self._cursor = self._conn.cursor(MySQLdb.cursors.DictCursor)
	# 	return (self._conn, self._cursor)
	# 
	# def __exit__(self, type, value, traceback):
	# 	self._cursor.close()
	# 	self._conn.close()
