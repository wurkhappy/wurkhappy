import smtplib

class EmailConnectionError(Exception):
	def __init__(self, expr, msg):
		self.expr = expr
		self.msg = msg
		

class Email (object):
	settings = {}
		
	def __init__(self, settings):
		self.settings = settings
		
# -------------------------------------------------------------------
# Send an email
# -------------------------------------------------------------------
	
	def sendmail(self, from_e, from_u, to_e, subject, body):
		if not self.settings:
			raise EmailConnectionError
		else:
			server = None
			if self.settings.has_key('port'):
				server = smtplib.SMTP(self.settings['host'], self.settings['port'])
			else:
				server = smtplib.SMTP(self.settings['host'])
			server.ehlo()
			server.starttls()
			server.ehlo()
			server.login(self.settings['user'], self.settings['password'])
			
			header = 'To:' + to_e + '\n' + 'From:' + from_u + '\n' + 'Subject:' + subject + '\n'
			message = header + '\n\n' + body

			server.sendmail(from_e, to_e, message)
			server.quit()
			
	def sendFromApp(self, to_e, subject, body):
		self.sendmail('wurk@happy.com', self.settings['from'], to_e, subject, body)

