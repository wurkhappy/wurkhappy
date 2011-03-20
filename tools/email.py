import smtplib

class EmailConnectionError(Exception):
	def __init__(self, expr, msg):
		self.expr = expr
		self.msg = msg
		

class Email (object):
	settings = {}
		
	@classmethod
	def configure(clz, settings):
		clz.settings = settings
		
# -------------------------------------------------------------------
# Send an email
# -------------------------------------------------------------------
	@classmethod
	def sendmail(clz, from_e, from_u, to_e, subject, body):
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
			
			header = 'To:' + to_e + '\n' + 'From:' + from_u + '\n' + 'Subject:' + subject + '\n'
			message = header + '\n\n' + body

			server.sendmail(from_e, to_e, message)
			server.quit()
	
	@classmethod		
	def sendFromApp(clz, to_e, subject, body):
		clz.sendmail('wurk@happy.com', clz.settings['from'], to_e, subject, body)

