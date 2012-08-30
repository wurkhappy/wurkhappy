from models.user import User, UserState, UserToken, ActiveUserState, NewUserState, InvitedUserState, BetaUserState
from models.agreement import Agreement, AgreementPhase
from models.request import Request
from models.transaction import Transaction
from models.paymentmethod import PaymentMethod
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
	def __init__(self, application):
		self.application = application
		
		# TODO: This should be set in a config file.
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
				# According to RFC 2046, the last part of a multipart message,
				# in this case the HTML message, is best and preferred.
				msg.attach(MIMEText(content, mimeType))
			
			server.sendmail(message['from'][1], message['to'][1], msg.as_string())
		



class TestHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])
		
		if user:
			logging.info(json.dumps({
				"message": "Test hook recieved user",
				"actionType": body['action'],
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
		
		token = Verification.generateHashDigest()
		
		userToken = UserToken(userID=client['id'])
		userToken.setTokenHash(token)
		userToken.save()
		
		vendor = User.retrieveByID(agreement['vendorID'])
		
		data = {
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'agreement': agreement.getPublicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		data['agreement']['token'] = token
		
		t = self.loader.load('agreement_new_user.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just sent you an estimate using Wurk Happy" % vendor.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		# TODO: This defeats the function of an invitation to prevent it from going out to
		# non-registered users, but we're keeping things closed for now...
		
		# Turning this off for now... Let's see what happens.
		
		# if not isinstance(client.getCurrentState(), ActiveUserState):
		# 	logging.warn(json.dumps({
		# 		"message": "Attempted to send message to invalid user",
		# 		"actionType": body['action'],
		# 		"recipientID": client['id'],
		# 		"recipientEmail": client['email'],
		# 		"agreementID": agreement['id']
		# 	}))
		# 	
		# 	return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=vendor.getFullName()), "contact@wurkhappy.com"),
			'to': (client.getFullName(), client['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		agreement.save()
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
			"recipientID": client['id'],
			"recipientEmail": client['email'],
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
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'agreement': agreement.getPublicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('agreement_send.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just sent you an estimate using Wurk Happy" % vendor.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		if not isinstance(client.getCurrentState(), ActiveUserState):
			logging.warn(json.dumps({
				"message": "Attempted to send message to invalid user",
				"actionType": body['action'],
				"recipientID": client['id'],
				"recipientEmail": client['email'],
				"agreementID": agreement['id']
			}))
			
			return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=vendor.getFullName()), "contact@wurkhappy.com"),
			'to': (client.getFullName(), client['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
			"recipientID": client['id'],
			"recipientEmail": client['email'],
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
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'agreement': agreement.getPublicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('agreement_accept.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just accepted your proposed agreement on Wurk Happy" % client.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		if not isinstance(vendor.getCurrentState(), ActiveUserState):
			logging.warn(json.dumps({
				"message": "Attempted to send message to invalid user",
				"actionType": body['action'],
				"recipientID": vendor['id'],
				"recipientEmail": vendor['email'],
				"agreementID": agreement['id']
			}))
			
			return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=client.getFullName()), "contact@wurkhappy.com"),
			'to': (vendor.getFullName(), vendor['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
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
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'agreement': agreement.getPublicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('agreement_change.html')
		htmlString = t.generate(data=data)
		
		subject = "%s requested changes to your proposed agreement on Wurk Happy" % client.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		if not isinstance(vendor.getCurrentState(), ActiveUserState):
			logging.warn(json.dumps({
				"message": "Attempted to send message to invalid user",
				"actionType": body['action'],
				"recipientID": vendor['id'],
				"recipientEmail": vendor['email'],
				"agreementID": agreement['id']
			}))
			
			return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=client.getFullName()), "contact@wurkhappy.com"),
			'to': (vendor.getFullName(), vendor['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
			"recipientID": vendor['id'],
			"recipientEmail": vendor['email'],
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
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'agreement': agreement.getPublicDict(),
			'phase': phase.getPublicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('agreement_work_complete.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just completed a phase of work on your agreement on Wurk Happy" % vendor.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		if not isinstance(client.getCurrentState(), ActiveUserState):
			logging.warn(json.dumps({
				"message": "Attempted to send message to invalid user",
				"actionType": body['action'],
				"recipientID": client['id'],
				"recipientEmail": client['email'],
				"agreementID": agreement['id']
			}))
			
			return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=vendor.getFullName()), "contact@wurkhappy.com"),
			'to': (client.getFullName(), client['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
			"recipientID": client['id'],
			"recipientEmail": client['email'],
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
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'agreement': agreement.getPublicDict(),
			'phase': phase.getPublicDict(),
			'paymentMethod': paymentMethod.getPublicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('agreement_pay.html')
		htmlString = t.generate(data=data)
		
		subject = "%s just submitted payment via Wurk Happy" % client.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		if not isinstance(vendor.getCurrentState(), ActiveUserState):
			logging.warn(json.dumps({
				"message": "Attempted to send message to invalid user",
				"actionType": body['action'],
				"recipientID": vendor['id'],
				"recipientEmail": vendor['email'],
				"agreementID": agreement['id']
			}))
			
			return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=client.getFullName()), "contact@wurkhappy.com"),
			'to': (vendor.getFullName(), vendor['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
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
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'agreement': agreement.getPublicDict(),
			'phase': phase.getPublicDict()
		}
		
		data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('agreement_dispute.html')
		htmlString = t.generate(data=data)
		
		subject = "%s needs more information about the work you completed" % client.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		if not isinstance(vendor.getCurrentState(), ActiveUserState):
			logging.warn(json.dumps({
				"message": "Attempted to send message to invalid user",
				"actionType": body['action'],
				"recipientID": vendor['id'],
				"recipientEmail": vendor['email'],
				"agreementID": agreement['id']
			}))
			
			return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=client.getFullName()), "contact@wurkhappy.com"),
			'to': (vendor.getFullName(), vendor['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
			"vendorID": vendor['id'],
			"vendorEmail": vendor['email'],
			"agreementID": agreement['id']
		}))



class SendAgreementRequestHandler(QueueHandler):
	def receive(self, body):
		request = Request.retrieveByID(body['requestID'])
		# agreement = Agreement.retrieveByID(body['agreementID'])
		
		if not request:
			raise Exception("No such request")
		
		client = User.retrieveByID(request['clientID'])
		vendor = User.retrieveByID(request['vendorID'])
		# phase = AgreementPhase.retrieveByID(body['agreementPhaseID'])
		
		data = {
			'hostname': self.application.config['wurkhappy']['hostname'],
			'client': client.getPublicDict(),
			'vendor': vendor.getPublicDict(),
			'request': request.getPublicDict()
			# 'phase': phase.getPublicDict()
		}
		
		# data['agreement']['phases'] = list(AgreementPhase.iteratorWithAgreementID(agreement['id']))
		
		t = self.loader.load('request_proposal.html')
		htmlString = t.generate(data=data)
		
		subject = "%s requested an agreement proposal from you" % client.getFullName()
		# TODO: work on this so the plaintext version is a parallel version of the HTML
		# (We might have pairs of templates or something...)
		textString = "If you cannot view the message, sign in to Wurk Happy at http://{0}/".format(data['hostname'])
		
		if not isinstance(vendor.getCurrentState(), ActiveUserState):
			logging.warn(json.dumps({
				"message": "Attempted to send message to invalid user",
				"actionType": body['action'],
				"recipientID": vendor['id'],
				"recipientEmail": vendor['email'],
				"requestID": request['id']
			}))
			
			return
		
		self.sendEmail({
			'from': ("{name} via Wurk Happy".format(name=client.getFullName()), "contact@wurkhappy.com"),
			'to': (vendor.getFullName(), vendor['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			"message": "Successfully sent email",
			"actionType": body['action'],
			"vendorID": vendor['id'],
			"vendorEmail": vendor['email'],
			"requestID": request['id']
		}))



class UserInviteHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])
		
		if not user:
			raise Exception("No such user")
		
		if not isinstance(user.getCurrentState(), (NewUserState, InvitedUserState, BetaUserState)):
			raise Exception("User may not be invited")
		
		digest = Verification.generateHashDigest()
		host = self.application.config['wurkhappy']['hostname']
		
		userToken = UserToken(userID=user['id'])
		userToken.setTokenHash(digest)
		userToken.save()
		
		data = {
			'hostname': host,
			'user': user.getPublicDict(),
			'url': 'http://{0}/account/setup?t={1}'.format(host, digest)
		}
		
		t = self.loader.load('user_invite.html')
		htmlString = t.generate(data=data)
		
		subject = "Get started with Wurk Happy!"
		textString = '''Dear Wurk Happy Customer,

Thank you for your interest in Wurk Happy! We enable freelancers and their
clients to negotiate contracts, manage the working relationship and get paid,
all in one easy place.

To get started with your account, please verify your email address by
either the link below or copying and pasting it in your browser.

{0}

If you have questions or comments, you can reach us at

contact@wurkhappy.com

Sincerely,
The Wurk Happy Team
'''.format(data['url'])
		
		self.sendEmail({
			'from': ('Wurk Happy', 'contact@wurkhappy.com'),
			'to': (user.getFullName(), user['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})
		
		logging.info(json.dumps({
			'message': 'Successfully sent email',
			'actionType': body['action'],
			'recipientID': user['id'],
			'recipientEmail': user['email']
		}))



class UserResetPasswordHandler(QueueHandler):
	def receive(self, body):
		user = User.retrieveByID(body['userID'])
		
		if not user:
			raise Exception("No such user")
		
		if not isinstance(user.getCurrentState(), ActiveUserState):
			raise Exception("User may not reset password")
		
		digest = Verification.generateHashDigest()
		host = self.application.config['wurkhappy']['hostname']
		
		userToken = UserToken(userID=user['id'])
		userToken.setTokenHash(digest)
		userToken.save()
		
		# user.setConfirmationHash(digest)
		# user['password'] = None
		# user.save()
		
		data = {
			'hostname': host,
			'user': user.getPublicDict(),
			'url': 'http://{0}/user/me/password?t={1}'.format(host, digest)
		}
		
		t = self.loader.load('user_reset_password.html')
		htmlString = t.generate(data=data)
		
		subject = "Reset your Wurk Happy password"
		textString = '''
Hello, {0}.

To reset the password on your Wurk Happy account, please verify your
email address by following the link below.

{1}

Please contact us if you need further assistance.

contact@wurkhappy.com

Thanks,
The Wurk Happy Team
'''.format(data['user']['fullName'], data['url'])

		self.sendEmail({
			'from': ('Wurk Happy', 'contact@wurkhappy.com'),
			'to': (user.getFullName(), user['email']),
			'subject': subject,
			'multipart': [
				(textString, 'text'),
				(htmlString, 'html')
			]
		})

		logging.info(json.dumps({
			'message': 'Successfully sent email',
			'actionType': body['action'],
			'recipientID': user['id'],
			'recipientEmail': user['email']
		}))
