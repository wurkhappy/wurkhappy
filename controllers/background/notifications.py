from models.user import User
from models.agreement import Agreement, AgreementPhase
from models.transaction import Transaction
from controllers.email import Email
from controllers.orm import ORMJSONEncoder
from controllers.verification import Verification

import tornado.template as template
import json
import logging
import hashlib

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



class QueueHandler(object):
	def __init__(self):
		# @todo: This should be set in a config file.
		self.loader = template.Loader('templates/notification')
	
	def sendEmail(self, message):
		"""
		QueueHandler.sendEmail takes a dictionary in the form described below
		and sends a MIME multipart/alternative formatted email to the specified
		recipient using the email server configuration from the application
		settings.
		
		{
			'from': (senderName, senderAddress),
			'to': (recipientName, recipientAddress),
			'subject': subject,
			'multipart': [
				(textPart, 'plain'),
				(htmlPart, 'html')
			]
		}
		
		Optionally, instead of the multipart list, a single 'content' string
		may be included.
		"""
		
		with Email() as (server):
			# Create message container - the correct MIME type is multipart/alternative.
			msg = MIMEMultipart('alternative')
			msg['Subject'] = message['subject']
			msg['From'] = message['from'][0]
			msg['To'] = message['to'][0]
			
			# Record the MIME types of each part - (usually text/plain and text/html)
			for (content, mimeType) in message['multipart']:
				# Attach parts into message container.
				# According to RFC 2046, the last part of a multipart message, in this case
				# the HTML message, is best and preferred.
				msg.attach(MIMEText(content, mimeType))
			
			server.sendmail(message['from'][1], message['to'][1], msg.as_string())
		



class InviteHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])
		
		if user:
			logging.info(json.dumps({
				"message": "Test hook recieved user",
				"userID": user['id'],
				"userName": user.getFullName(),
				"userEmail": user['email']
			}))
		else:
			raise Exception("No such user")



class AgreementInviteHandler(QueueHandler):
	def receive(self, body):
		client = User.retrieveByID(body['userID'])
		agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not client:
			raise Exception("No such user")
		
		if not agreement:
			raise Exception("No such agreement")
		
		if agreement['tokenFingerprint']:
			raise Exception("We already did this agreement")
		
		verify = Verification()
		
		agreement['tokenFingerprint'] = hashlib.md5(verify.hashDigest).hexdigest()
		agreement.setTokenHash(verify.hashDigest)
		
		vendor = User.retrieveByID(agreement['vendorID'])
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		data['agreement']['token'] = verify.hashDigest
		
		t = self.loader.load('agreement_new_user.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just sent you an estimate using Wurk Happy" % vendor.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		
		with Email() as (server):
			senderName = "Wurk Happy Community"
			# @todo: Replace this line with "recipientAddress = client['email']" for production deployment
			recipientAddress = client['email'] if client['email'].endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
			
			# Create message container - the correct MIME type is multipart/alternative.
			msg = MIMEMultipart('alternative')
			msg['Subject'] = subject
			msg['From'] = senderName
			msg['To'] = recipientAddress
			
			# @todo: Something sensible here, please...
			# Create the body of the message (a plain-text and an HTML version).
			text = "If you cannot view the message, go to http://www.wurkhappy.com/ and type 'foo'."
			html = htmlString

			# Record the MIME types of both parts - text/plain and text/html.
			part1 = MIMEText(text, 'plain')
			part2 = MIMEText(html, 'html')

			# Attach parts into message container.
			# According to RFC 2046, the last part of a multipart message, in this case
			# the HTML message, is best and preferred.
			msg.attach(part1)
			msg.attach(part2)
			
			server.sendmail("contact@wurkhappy.com", recipientAddress, msg.as_string())
		
		agreement.save()
		agreement.refresh()
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"clientID": client['id'],
			"clientEmail": client['email'],
			"agreementID": agreement['id']
		}))



class AgreementSentHandler(QueueHandler):
	def receive(self, body):
		client = User.retrieveByID(body['userID'])
		agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not client:
			raise Exception("No such user")
		
		if not agreement:
			raise Exception("No such agreement")
		
		vendor = User.retrieveByID(agreement['vendorID'])
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('agreement_send.html')
		htmlString = t.generate(data=data)

		subject = "%s just sent you an estimate using Wurk Happy" % vendor.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, go to http://www.wurkhappy.com/ and type 'foo'."
		
		recipientAddress = client['email'] if client['email'].endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
		
		self.sendEmail({
			'from': ("{0} (via Wurk Happy)".format(vendor.getFullName()), "contact@wurkhappy.com"),
			# 'to': (client.getFullName(), client['email']),
			'to': (client.getFullName(), recipientAddress),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		agreement.save()
		#agreement.refresh()
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"clientID": client['id'],
			"clientEmail": client['email'],
			"agreementID": agreement['id']
		}))



class AgreementAcceptedHandler(QueueHandler):
	def receive(self, body):
		vendor = User.retrieveByID(body['userID'])
		agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not vendor:
			raise Exception("No such user")
		
		if not agreement:
			raise Exception("No such agreement")
		
		client = User.retrieveByID(agreement['clientID'])
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict()
		}
		
		t = self.loader.load('agreement_accept.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just accepted your proposed agreement on Wurk Happy" % client.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, go to http://www.wurkhappy.com/ and type 'foo'."
		
		recipientAddress = vendor['email'] if vendor['email'].endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
		
		self.sendEmail({
			'from': ("{0} (via Wurk Happy)".format(client.getFullName()), "contact@wurkhappy.com"),
			# 'to': (client.getFullName(), client['email']),
			'to': (vendor.getFullName(), recipientAddress),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"vendorID": vendor['id'],
			"vendorEmail": vendor['email'],
			"agreementID": agreement['id']
		}))



class AgreementDeclinedHandler(QueueHandler):
	def receive(self, body):
		vendor = User.retrieveByID(body['userID'])
		agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not vendor:
			raise Exception("No such user")
		
		if not agreement:
			raise Exception("No such agreement")
		
		client = User.retrieveByID(agreement['clientID'])
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict()
		}
		
		t = self.loader.load('agreement_change.html')
		htmlString = t.generate(data=data)
		
		subject = "%s requested changes to your proposed agreement on Wurk Happy" % client.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, go to http://www.wurkhappy.com/ and type 'foo'."
		
		recipientAddress = vendor['email'] if vendor['email'].endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
		
		self.sendEmail({
			'from': ("{0} (via Wurk Happy)".format(client.getFullName()), "contact@wurkhappy.com"),
			# 'to': (vendor.getFullName(), vendor['email']),
			'to': (vendor.getFullName(), recipientAddress),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"vendorID": vendor['id'],
			"vendorEmail": vendor['email'],
			"agreementID": agreement['id']
		}))



class AgreementWorkCompletedHandler(QueueHandler):
	def receive(self, body):
		client = User.retrieveByID(body['userID'])
		
		if not client:
			raise Exception("No such user")
		
		agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not agreement:
			raise Exception("No such agreement")
		
		phase = AgreementPhase.retrieveByID(body['agreementPhaseID'])
		vendor = User.retrieveByID(agreement['vendorID'])
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict(),
			'phase': phase.publicDict()
		}
		
		t = self.loader.load('agreement_work_complete.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just completed a phase of work on your agreement on Wurk Happy" % vendor.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, go to http://www.wurkhappy.com/ and type 'foo'."
		
		recipientAddress = client['email'] if client['email'].endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
		
		self.sendEmail({
			'from': ("{0} (via Wurk Happy)".format(vendor.getFullName()), "contact@wurkhappy.com"),
			# 'to': (client.getFullName(), client['email']),
			'to': (client.getFullName(), recipientAddress),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"clientID": client['id'],
			"clientEmail": client['email'],
			"agreementID": agreement['id']
		}))



class AgreementPaidHandler(QueueHandler):
	def receive(self, body):
		vendor = User.retrieveByID(body['userID'])
		
		if not vendor:
			raise Exception("No such user")
		
		agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not agreement:
			raise Exception("No such agreement")
		
		client = User.retrieveByID(agreement['clientID'])
		transaction = Transaction.retrieveByID(body['transactionID'])
		phase = AgreementPhase.retrieveByID(transaction['agreementPhaseID'])
		paymentMethod = PaymentMethod.retrieveByID(transaction['paymentMethodID'])
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict(),
			'phase': phase.publicDict(),
			'paymentMethod': paymentMethod.publicDict()
		}
		
		t = self.loader.load('agreement_pay.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just submitted payment via Wurk Happy" % client.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, go to http://www.wurkhappy.com/ and type 'foo'."
		
		recipientAddress = vendor['email'] if vendor['email'].endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
		
		self.sendEmail({
			'from': ("{0} (via Wurk Happy)".format(client.getFullName()), "contact@wurkhappy.com"),
			# 'to': (vendor.getFullName(), vendor['email']),
			'to': (vendor.getFullName(), recipientAddress),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"vendorID": vendor['id'],
			"vendorEmail": vendor['email'],
			"agreementID": agreement['id']
		}))



class AgreementDisputedHandler(QueueHandler):
	def receive(self, body):
		vendor = User.retrieveByID(body['userID'])
		agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not vendor:
			raise Exception("No such user")
		
		if not agreement:
			raise Exception("No such agreement")
		
		client = User.retrieveByID(agreement['clientID'])
		phase = AgreementPhase.retrieveByID(body['agreementPhaseID'])
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict(),
			'phase': phase.publicDict()
		}
		
		t = self.loader.load('agreement_dispute.html')
		htmlString = t.generate(data=data)
		
		subject = "%s needs more information about the work you completed" % client.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, go to http://www.wurkhappy.com/ and type 'foo'."
		
		recipientAddress = vendor['email'] if vendor['email'].endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
		
		self.sendEmail({
			'from': ("{0} (via Wurk Happy)".format(client.getFullName()), "contact@wurkhappy.com"),
			# 'to': (vendor.getFullName(), vendor['email']),
			'to': (vendor.getFullName(), recipientAddress),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"vendorID": vendor['id'],
			"vendorEmail": vendor['email'],
			"agreementID": agreement['id']
		}))
