from beanstalkc import Connection, Job



class BeanstalkConnectionError(Exception):
	pass


class AsyncBeanstalk(object):
	pass

class Beanstalk(object):
	settings = {}
	
	@classmethod
	def configure(clz, settings, tag=None):
		clz.settings[tag] = settings
	
	def __init__(self, tag=None):
		self._tag = tag if tag in self.settings else None
	
	def __enter__(self):
		if self._tag not in self.settings:
			raise BeanstalkConnectionError('beanstalkd is not configured')
		
		self._conn = Connection(self.settings[self._tag]['host'], self.settings[self._tag]['port'])
		
		# if self._tube:
		# 	self._conn.use(tube)
		# 
		return (self._conn)
	
	def __exit__(self, type, value, traceback):
		# Be a good guest and clean up after yourself. Just realized this is *soooo* not threadsafe.
		self._conn.close()