import smtplib

class EmailConnectionError(Exception):
	def __init__(self, expr, msg):
		self.expr = expr
		self.msg = msg
		

class Email (object):
	settings = {}
		
	@classmethod
	def configure(clz, settings, tag=None):
		clz.settings[tag] = settings
	
	def __init__(self, tag=None):
		self._tag = tag if tag in self.settings else None
	
	def __enter__(self):
		if self._tag not in self.settings:
			raise EmailConnectionError('email is not configured')
		
		conf = self.settings[self._tag]
		
		if 'port' in conf:
			self._server = smtplib.SMTP(conf['host'], conf['port'])
		else:
			self._server = smtplib.SMTP(conf['host'])
		
		self._server.ehlo()
		self._server.starttls()
		self._server.ehlo()
		self._server.login(conf['user'], conf['password'])
		
		return (self._server)

	def __exit__(self, type, value, traceback):
		# Be a good guest and clean up after yourself. Just realized this is *soooo* not threadsafe.
		self._server.quit()
	
	# -------------------------------------------------------------------
	# Send an email
	# -------------------------------------------------------------------
	@classmethod
	def sendmail(clz, from_e, from_u, to_e, subject, body):
		'''Opens an SMTP connection with the server specified in settings
			 and assembles a message to be sent, then closes the connection'''

		if not clz.settings:
			raise EmailConnectionError
		else:
			server = None
			if clz.settings.has_key('port'):
				server = smtplib.SMTP(clz.settings['host'], clz.settings['port'])
			else:
				server = smtplib.SMTP(clz.settings['host'])
			server.ehlo()
			server.starttls()
			server.ehlo()
			server.login(clz.settings['user'], clz.settings['password'])
			
			headers = {
				'To': to_e,
				'From': from_u,
				'Subject': subject
			}
			
			headerString = '\n'.join(["%s:%s" % (k, v) for k, v in headers.iteritems()])
			message = headerString + '\n\n' + body
			
			server.sendmail(from_e, to_e, message)
			server.quit()
	
	@classmethod
	def sendFromApp(clz, to_e, subject, body):
		clz.sendmail('wurk@happy.com', clz.settings['from'], to_e, subject, body)

