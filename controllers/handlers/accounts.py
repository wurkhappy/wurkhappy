from __future__ import division

from base import *
from models.user import User, UserPrefs
from models.paymentmethod import PaymentMethod
from controllers import fmt

import json
import logging
import os

from datetime import datetime

# Required for resizing profile image uploads
import Image, ImageOps
from StringIO import StringIO

# Required for generating remote resource ID strings (S3 keys)
import uuid
from hashlib import sha1
from controllers.base import Base16, Base58

# Required for uploading images to S3
from controllers.amazonaws import AmazonS3
from boto.s3.key import Key

# -------------------------------------------------------------------
# AccountHandler
# -------------------------------------------------------------------

class AccountHandler(Authenticated, BaseHandler):

	@web.authenticated
	def get(self):
		# inherited from web.RequestHandler:
		user = self.current_user
		
		# userProfile = user.getProfile()
		
		userDict = {
			'_xsrf': self.xsrf_token,
			'id': user.id,
			'firstName': user.firstName,
			'lastName': user.lastName,
			'fullName': user.getFullName(),
			'email': user.email,
			'telephone': user.telephone or '',
			'profileURL': [
				user.profileSmallURL or '#',
				user.profileLargeURL or '#'
			],
			'self': 'account'
		}
		
		paymentMethod = PaymentMethod.retrieveACHMethodWithUserID(user.id)
		
		if paymentMethod:
			userDict['storedBank'] = paymentMethod.publicDict()
		
		paymentMethod = PaymentMethod.retrieveCCMethodWithUserID(user.id)
		
		if paymentMethod:
			userDict['storedCard'] = paymentMethod.publicDict()
		
		self.render('user/account.html', 
			title="Wurk Happy &ndash; My Account", data=userDict
		)
	
	@web.authenticated
	def post(self):
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				#TODO: Enforce email and telephone formats
				optional=[
					('firstName', fmt.Enforce(str)),
					('lastName', fmt.Enforce(str)),
					('email', fmt.Email()),
					('telephone', fmt.PhoneNumber())
				],
				required=[]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		#TODO: this should probably be handled in a better way. We'll
		# worry about that when we do cleanup and robustification.



# -------------------------------------------------------------------
# AccountJSONHandler
# -------------------------------------------------------------------

class AccountJSONHandler(Authenticated, BaseHandler):

	@web.authenticated
	def post(self):
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('firstName', fmt.Enforce(str)),
					('lastName', fmt.Enforce(str)),
					('email', fmt.Email()),
					('telephone', fmt.PhoneNumber())
				],
				required=[]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		# @todo:
		# The HTTPErrorBetter raised by fmt.Parser could be, uhh, better.
		# Errors that are responses to AJAX calls include a display message
		# that is intended to be helpful to the user, in addition to 
		# machine-parseable error identifiers.
		# 
		# error = {
		# 	'domain': 'web.request',
		# 	'display': (
		# 		"I'm sorry, that didn't look like a proper email "
		# 		"address. Could you please enter a valid email address?"
		# 	),
		# 	'debug': "'email' parameter value must be well-formed"
		# }
		
		user.email = args['email'] or user.email
		user.firstName = args['firstName'] or user.firstName
		user.lastName = args['lastName'] or user.lastName
		user.telephone = args['telephone'] or user.telephone
		
		# @todo: This needs refactoring
		if 'profilePhoto' in self.request.files:
			fileDict = self.request.files['profilePhoto'][0]
			base, ext = os.path.splitext(fileDict['filename'])
			
			imgs = {
				'o': None,
				's': None,
				'l': None
			}
			
			params = {
				'o': ('profileOrigURL', 75),
				's': ('profileSmallURL', 95),
				'l': ('profileLargeURL', 85)
			}
			
			headers = {'Content-Type': fileDict['content_type']}
			
			try:
				imgs['o'] = Image.open(StringIO(fileDict['body']))
			except IOError as e:
				error = {
					'domain': 'web.request',
					'display': (
						"I'm sorry, that image was either damaged or "
						"unrecognized. Could you please try to upload "
						"it again?"
					),
					'debug': 'cannot identify image file'
				}
				
				raise HTTPErrorBetter(400, "Failed to read image", 
					json.dumps(error))
			
			imgs['s'] = ImageOps.fit(imgs['o'], (50, 50), Image.ANTIALIAS)
			imgs['l'] = ImageOps.fit(imgs['o'], (150, 150), Image.ANTIALIAS)
			
			hashString = Base58(Base16(sha1(uuid.uuid4().bytes).hexdigest())).string
			nameFormat = '%s_%%s.jpg' % hashString
			
			with AmazonS3() as (conn, bucket):
				for t, v in imgs.iteritems():
					imgData = StringIO()
					v.save(imgData, 'JPEG', quality=params[t][1])
					
					k = Key(bucket)
					k.key = nameFormat % t
					k.set_contents_from_string(imgData.getvalue(), headers)
					k.make_public()
					
					user.__dict__[params[t][0]] = 'http://media.wurkhappy.com/' + nameFormat % t
		
		user.save()
		logging.warn(user.publicDict())
		self.renderJSON(user.publicDict())



# -------------------------------------------------------------------
# PasswordJSONHandler
# -------------------------------------------------------------------

class PasswordJSONHandler(Authenticated, BaseHandler):

	@web.authenticated
	def post(self):
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('currentPassword', fmt.Enforce(str)),
					('newPassword', fmt.Enforce(str)),
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		if not (user and user.passwordIsValid(args['old_password'])):
			# User wasn't found, or password is wrong, display error
			#TODO: Exponential back-off when user enters incorrect password.
			#TODO: Flag accounds if passwords change too often.
			error = {
				"domain": "web.request",
				"debug": "please validate authentication credentials"
			}
			self.set_status(401)
			self.renderJSON(error)
		else:
			user.setPasswordHash(args['new_password'])
			user.save()
			self.write(json.dumps({"success": True}))



# -------------------------------------------------------------------
# NewPaymentMethodJSONHandler
# -------------------------------------------------------------------
# Creates new payment methods; either ACH or credit card. Returns
# 201 on success with JSON repr of the new method and a Location
# header for the newly created resource.

class NewPaymentMethodJSONHandler(Authenticated, BaseHandler):
	@web.authenticated
	def post(self):
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					# @todo: create routing, account number formatters
					('routingNumber', fmt.Enforce(str)),
					('accountNumber', fmt.Enforce(str)),
					
					# @todo: create CC number formatter
					('cardNumber', fmt.Enforce(str)),
					('expirationMonth', fmt.Enforce(int)),
					('expirationYear', fmt.Enforce(int)),
					('verification', fmt.Enforce(str))
				],
				required=[]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		paymentMethod = None
		
		if args['routingNumber'] and args['accountNumber']:
			paymentMethod = PaymentMethod.retrieveACHMethodWithUserID(user.id)
		
			# @todo: this is hackety until we actually verify this info through
			# a payment gateway
		
			abaDisplay = args['routingNumber'][-3:]
			accountDisplay = args['accountNumber'][-4:]
		
			if paymentMethod:
				# Mark any existing payment method unused
				paymentMethod.dateDeleted = datetime.now()
				paymentMethod.save()
		
			paymentMethod = PaymentMethod.initWithDict(dict(
				userID=user.id,
				display=accountDisplay,
				abaDisplay=abaDisplay
			))
		elif args['cardNumber'] and args['verification']:
			paymentMethod = PaymentMethod.retrieveCCMethodWithUserID(user.id)
		
			if paymentMethod:
				# Mark any existing payment method unused
				paymentMethod.dateDeleted = datetime.now()
				paymentMethod.save()
		
			# @todo: this is hackety until we actually verify this info through
			# a payment gateway
		
			displayString = args['cardNumber'][-4:]
		
			# Assemble a human-readable string of the expiration month and year
			cardExpiration = "%s %d" % ([
				'January',
				'February',
				'March',
				'April',
				'May',
				'June',
				'July',
				'August',
				'September',
				'October',
				'November',
				'December'
			][args['expirationMonth'] - 1], args['expirationYear'])
		
		
			paymentMethod = PaymentMethod.initWithDict(dict(
				userID=user.id,
				display=displayString,
				cardExpires=cardExpiration
			))
		else:
			# @todo: Handle this error. there were not proper args
			error = {
				"domain": "web.request",
				"display": "",
				"debug": "00C1S"
			}
			self.set_status(400)
			self.renderJSON(error)
			return
		
		paymentMethod.save()
		paymentMethod.refresh()
		
		result = paymentMethod.publicDict()
		locationStr = 'http://%s/user/me/paymentmethod/%d.json' % (
			self.request.host, paymentMethod.id
		)
		
		self.set_status(201)
		self.set_header('Location', locationStr)
		self.renderJSON(result)



# -------------------------------------------------------------------
# PaymentMethodJSONHandler
# -------------------------------------------------------------------
# Retrieves the JSON representation of a specific payment method or
# deletes said method.

class PaymentMethodJSONHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self, paymentMethodID):
		user = self.current_user
		paymentMethod = PaymentMethod.retrieveByID(paymentMethodID)
		
		if paymentMethod.userID != user.id:
			# The user is not authorized to see it
			error = {
				"domain": "application.resource.not_found",
				"display": "The specified payment method could not be found.",
				"debug": "no such resource"
			}
			self.set_status(404)
			self.renderJSON(error)
		
		self.renderJSON(paymentMethod.publicDict())
	
	@web.authenticated
	def delete(self, paymentMethodID):
		user = self.current_user
		
		paymentMethod = PaymentMethod.retrieveByID(paymentMethodID)
		
		if not paymentMethod:
			error = {
			# @todo: FIX THIS PLEASE
				"domain": "",
				"display": "",
				"debug": ""
			}
			self.set_status(400)
			self.renderJSON(error)
		
		paymentMethod.dateDeleted = datetime.now()
		paymentMethod.save()
		
		self.renderJSON([True])
