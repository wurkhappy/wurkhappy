from models.user import User
from models.agreement import Agreement
from controllers.email import Email
from controllers.orm import ORMJSONEncoder
from controllers.verification import Verification

import tornado.template as template
import json
import logging
import sys
import hashlib

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



class QueueHandler(object):
	def __init__(self):
		# @todo: This should be set in a config file.
		self.loader = template.Loader('templates/notification')



class InviteHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])
		
		if user:
			logging.info(json.dumps({
				"message": "Test hook recieved user",
				"userID": user.id,
				"userName": user.getFullName(),
				"userEmail": user.email
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
		
		if agreement.tokenFingerprint:
			raise Exception("We already did this agreement")
		
		verify = Verification()
		
		agreement.tokenFingerprint = hashlib.md5(verify.hashDigest).hexdigest()
		agreement.setTokenHash(verify.hashDigest)
		
		vendor = User.retrieveByID(agreement.vendorID)
		
		data = {
			'client': client.publicDict(),
			'vendor': vendor.publicDict(),
			'agreement': agreement.publicDict()
		}
		
		data['agreement']['token'] = verify.hashDigest
		
		t = self.loader.load('agreement_new_user.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just sent you an estimate using Wurk Happy" % vendor.getFullName()
		# @todo: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		
		with Email() as (server):
			senderName = "Wurk Happy Community"
			# @todo: Replace this line with "recipientAddress = client.email" for production deployment
			recipientAddress = client.email if client.email.endswith("wurkhappy.com") else "brendan+test@wurkhappy.com"
			
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
			"clientID": client.id,
			"clientEmail": client.email,
			"agreementID": agreement.id
		}))
