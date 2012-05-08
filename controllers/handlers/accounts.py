from __future__ import division

from base import *
from models.user import User, UserPrefs, UserDwolla, ActiveUserState
from models.paymentmethod import PaymentMethod
from controllers import fmt
from controllers.beanstalk import Beanstalk

from tornado.httpclient import HTTPClient, HTTPError

import json
import logging
import os

from datetime import datetime
import urlparse
import urllib
import functools

# Required to handle a potential database integrity error
from MySQLdb import IntegrityError

# Required for resizing profile image uploads
import Image, ImageOps
from StringIO import StringIO

# Required for generating remote resource ID strings (S3 keys)
import uuid
from hashlib import sha1
from controllers.data import Data, Base58

# Required for uploading images to S3
from controllers.amazonaws import AmazonS3
from boto.s3.key import Key



class DwollaRedirectMixin(object):
	def buildRedirectURL(self, token=None):
		return '{0}://{1}/user/me/connections{2}'.format(
			self.request.protocol,
			self.application.configuration['wurkhappy']['hostname'],
			'?t={0}'.format(token) if token else ''
		)

	def buildAuthorizeURL(self, token=None):
		return (
			'https://www.dwolla.com/oauth/v2/authenticate?'
			'client_id={0}&response_type=code&redirect_uri={1}&scope={2}'
		).format(
			self.application.configuration['dwolla']['key'],
			urllib.quote(self.buildRedirectURL(token), '/'),
			'transactions|balance|send|accountinfofull'
		)



# -------------------------------------------------------------------
# AccountHandler
# -------------------------------------------------------------------

class AccountHandler(TokenAuthenticated, BaseHandler, DwollaRedirectMixin):
	
	@web.authenticated
	def get(self):
		user = self.current_user
		token = self.token
		
		# If the user has provided a temporary token, display the
		# the user onboarding interface
		
		if token:
			dwollaAcct = UserDwolla.retrieveByUserID(user['id'])
			
			userDict = {
				'_xsrf': self.xsrf_token,
				'token': token,
				'id': user['id'],
				'firstName': user['firstName'],
				'lastName': user['lastName'],
				'email': user['email'],
				'telephone': user['telephone'] or '',
				'profileURL': [
					user['profileSmallURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg',
					user['profileLargeURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg'
				],
				'password': True if user['password'] else False,
				'dwolla': {
					'dwollaID': dwollaAcct and dwollaAcct['dwollaID'],
					'authorizeURL': self.buildAuthorizeURL(token)
				}
			}
			
			if user['dateVerified'] is None:
				user['dateVerified'] = datetime.now()
				user.save()
			
			self.clear_cookie('user_id')
			self.render('user/quickstart.html', title='Welcome to Wurk Happy', data=userDict)
			return
		
		# Otherwise, render the accounts page
		
		userDict = {
			'_xsrf': self.xsrf_token,
			# 'error': dwollaError,
			'id': user['id'],
			'firstName': user['firstName'],
			'lastName': user['lastName'],
			'fullName': user.getFullName(),
			'email': user['email'],
			'telephone': user['telephone'] or '',
			'profileURL': [
				user['profileSmallURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg',
				user['profileLargeURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg'
			],
			'self': 'account'
		}
		
		dwolla = UserDwolla.retrieveByUserID(user['id'])
		
		if dwolla:
			userDict['dwolla'] = dwolla.fields
		else:
			userDict['dwolla'] = {
				'dwollaID': None,
				'authorizeURL': self.buildAuthorizeURL()
			}
		
		self.render('user/account.html', 
			title="Wurk Happy &ndash; My Account", data=userDict
		)



# -------------------------------------------------------------------
# Account Connection Handler (Currently for Dwolla)
# -------------------------------------------------------------------

class AccountConnectionHandler(TokenAuthenticated, BaseHandler, DwollaRedirectMixin):
	@web.authenticated
	def get(self):
		"""This is a Dwolla callback handler. We are looking for the 'code'
		query string parameter to begin the token exchange process."""
		
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('code', fmt.Enforce(str))
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		if args['code']:
			# Do an HTTP request to get the token
			# It's synchronous for now, but we'll do async later.
			
			baseURL = 'https://www.dwolla.com/oauth/v2/token'
			queryArgs = {
			 	'client_id': self.application.configuration['dwolla']['key'],
				'client_secret': self.application.configuration['dwolla']['secret'],
				'grant_type': 'authorization_code',
				'redirect_uri': self.buildRedirectURL(self.token),
				'code': args['code']
			}
			queryString = '&'.join('{0}={1}'.format(key, urllib.quote(val, '/')) for key, val in queryArgs.iteritems())
			logging.info('Dwolla key exchange URL: %s', baseURL + '?' + queryString)
			
			httpClient = HTTPClient()
			
			# @TODO: UGLY HACK EW EW EW EW
			
			try:
				exchangeResponse = httpClient.fetch(baseURL + '?' + queryString)
			except HTTPError as e:
				logging.error('Dwolla token exchange returned an error: %s', e)
			else:
				# We don't trust third parties, so, like, log the entire response
				logging.info('Received %d from Dwolla', exchangeResponse.code)
				logging.info(exchangeResponse.body)
				
				if exchangeResponse.code == 200:
					# Parse the response body and store the access token
					responseDict = json.loads(exchangeResponse.body)
					oauthToken = responseDict['access_token']
					logging.info(oauthToken)
					accountURL = 'https://www.dwolla.com/oauth/rest/users/'
					queryString = 'oauth_token={0}'.format(urllib.quote(oauthToken, '/'))
					
					logging.info('Dwolla user info URL: %s', accountURL + '?' + queryString)
					
					try:
						accountResponse = httpClient.fetch(accountURL + '?' + queryString)
					except HTTPError as e:
						logging.error('Dwolla account lookup returned an error: %s', e)
					else:
						# We don't trust third parties, so, like, log the entire response
						logging.info('Received %d from Dwolla', accountResponse.code)
						logging.info(accountResponse.body)
						
						if accountResponse.code == 200:
							# Parse the second response body and update the DB
							accountDict = json.loads(accountResponse.body)
							
							if accountDict['Success'] == True:
								dwolla = UserDwolla()
								dwolla['userID'] = user['id']
								dwolla['userName'] = accountDict['Response']['Name']
								dwolla['dwollaID'] = accountDict['Response']['Id']
								dwolla['oauthToken'] = oauthToken
								dwolla.save()
							
								logging.info(dwolla)
							else:
								logging.error('Dwolla request failed. %s', accountDict)
								dwollaError = 'Wurk Happy was unable to connect with your Dwolla account.'
							
						else:
							logging.error('Dwolla account lookup returned an unexpected response. %s', accountResponse)
			
			# @TODO: If there was an error and you know it, clap your hands!
			
		self.set_status(200)
		self.set_secure_cookie("user_id", str(user['id']), httponly=True)
		self.write("""<html><body onload="window.close()"></body></html>""")
		return



# -------------------------------------------------------------------
# AccountJSONHandler
# -------------------------------------------------------------------
# TODO: FIGURE OUT TOKENS!
class AccountJSONHandler(TokenAuthenticated, BaseHandler):
	
	@web.authenticated
	def get(self):
		# TODO: TOKENS OK HERE
		user = self.current_user
		dwolla = UserDwolla.retrieveByUserID(user['id'])
		
		accountDict = user.getPublicDict()
		accountDict['dwolla'] = True if dwolla else False
		
		self.renderJSON(accountDict)
	
	@web.authenticated
	def post(self):
		# TODO: NO TOKENS HERE
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
		
		if args['email']:
			user['email'] = args['email']
			
			try:
				user.save()
			except IntegrityError as e:
				logging.warn(e.message)
				
				error = {
					"domain": "application.consistency",
					"display": (
						"The email address you submitted is in use by another "
						"member. Please provide a different email address."
					),
					"debug": "'email' parameter is already in use"
				}
				
				self.set_status(409)
				self.renderJSON(error)
				return
		
		if args['firstName']:
			user['firstName'] = args['firstName']
		if args['lastName']:
			user['lastName'] = args['lastName']
		if args['telephone']:
			user['telephone'] = args['telephone']
		
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
			
			# hashString = Base58(Base16(sha1(uuid.uuid4().bytes).hexdigest())).string
			hashString = Data(sha1(uuid.uuid4().bytes).digest()).stringWithEncoding(Base58)
			nameFormat = '%s_%%s.jpg' % hashString
			
			with AmazonS3() as (conn, bucket):
				for t, v in imgs.iteritems():
					imgData = StringIO()
					v.save(imgData, 'JPEG', quality=params[t][1])
					
					k = Key(bucket)
					k.key = nameFormat % t
					k.set_contents_from_string(imgData.getvalue(), headers)
					k.make_public()
					
					user[params[t][0]] = 'http://media.wurkhappy.com/' + nameFormat % t
		
		user.save()
		logging.warn(user.getPublicDict())
		self.renderJSON(user.getPublicDict())



# -------------------------------------------------------------------
# Password Recovery
# -------------------------------------------------------------------

class PasswordHandler(BaseHandler):
	'''Render the password recovery form or verify the token argument
	and render the password reset form. The form behavior is the same
	whether the user is authenticated with a cookie or not.'''
	
	def get(self):
		token = self.get_argument("t", None)
		
		if token:
			data = {
				'token': token,
				'_xsrf': self.xsrf_token
			}
			
			self.render('user/pw_reset.html', 
				title="Choose a New Password &ndash; Wurk Happy",
				data=data
			)
		else:
			data = {
				'_xsrf': self.xsrf_token
			}
			
			self.render('user/pw_forgot.html',
				title="Recover a Forgotten Password &ndash; Wurk Happy",
				data=data
			)



# -------------------------------------------------------------------
# Password Recovery JSON Handler
# -------------------------------------------------------------------

class PasswordRecoveryJSONHandler(BaseHandler):
	'''Responds to a POST request containing an email address, validates the
	address is a registered user and enqueues the request the request for the
	Notification Daemon.'''
	
	def post(self):
		
		try:
			args = fmt.Parser(self.request.arguments,
				required=[
					('email', fmt.Email())
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		user = User.retrieveByEmail(args['email'])
		
		if user and isinstance(user.getCurrentState(), ActiveUserState):
			msg = {
				'action': 'userResetPassword',
				'userID': user['id']
			}
		
			with Beanstalk() as bconn:
				tube = self.application.configuration['notifications']['beanstalk_tube']
				bconn.use(tube)
				r = bconn.put(json.dumps(msg))
				logging.info('Beanstalk: %s#%d %s' % (tube, r, msg))
		
		# We don't want hackers to use the response to determine which
		# email addresses we have on record, so we lie and return success,
		# even if the user didn't exist.
		
		# TODO: In the future, we should do pretty agressive rate limiting
		
		self.renderJSON({'success': True})



# -------------------------------------------------------------------
# PasswordJSONHandler
# -------------------------------------------------------------------

class PasswordJSONHandler(TokenAuthenticated, BaseHandler):

	@web.authenticated
	def post(self):
		user = self.current_user
		token = self.token
		
		if token:
			try:
				args = fmt.Parser(self.request.arguments,
					required=[
						('password', fmt.Enforce(str)),
					]
				)
			except Exception as e:
				# TODO: WHAT THE HELL WAS I THINKING HERE?!
				self.set_status(401)
				self.renderJSON(error)
				return
			
			user.setPasswordHash(args['password'])
			user.save()
			
			self.set_secure_cookie("user_id", str(user['id']), httponly=True)
			self.write(json.dumps({"success": True}))
			return
		
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
		
		if not (user and user.passwordIsValid(args['currentPassword'])):
			# User wasn't found, or password is wrong, display error
			#TODO: Exponential back-off when user enters incorrect password.
			#TODO: Flag accounds if passwords change too often.
			
			error = {
				"domain": "authentication",
				"display": (
					"The password you entered is incorrect. Please check "
					"for typos and make sure caps lock is turned off when "
					"entering your password."
				),
				"debug": "incorrect authentication credentials"
			}
			
			self.set_status(401)
			self.renderJSON(error)
		elif user.passwordIsValid(args['newPassword']):
			# New password is the same as old password, and that's bad.
			
			# TODO: This could expose a vector for a brute-force attack,
			# so we need to make sure that this cannot be called more than
			# say, five times per day...
			
			error = {
				"domain": "authentication.password",
				"display": (
					"Your new password cannot be the same as your current "
					"password. Please choose a different password."
				),
				"debug": "attempt to re-use password"
			}
			
			self.set_status(400)
			self.renderJSON(error)
		else:
			user.setPasswordHash(args['newPassword'])
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
			paymentMethod = PaymentMethod.retrieveACHMethodWithUserID(user['id'])
		
			# @todo: this is hackety until we actually verify this info through
			# a payment gateway
		
			abaDisplay = args['routingNumber'][-3:]
			accountDisplay = args['accountNumber'][-4:]
		
			if paymentMethod:
				# Mark any existing payment method unused
				paymentMethod['dateDeleted'] = datetime.now()
				paymentMethod.save()
		
			paymentMethod = PaymentMethod()
			paymentMethod['userID'] = user['id']
			paymentMethod['display'] = accountDisplay
			paymentMethod['abaDisplay'] = abaDisplay
		
		elif args['cardNumber'] and args['verification']:
			paymentMethod = PaymentMethod.retrieveCCMethodWithUserID(user['id'])
		
			if paymentMethod:
				# Mark any existing payment method unused
				paymentMethod['dateDeleted'] = datetime.now()
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
		
		
			paymentMethod = PaymentMethod()
			paymentMethod['userID'] = user['id']
			paymentMethod['display'] = displayString
			paymentMethod['cardExpires'] = cardExpiration
		
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
		
		result = paymentMethod.getPublicDict()
		locationStr = 'http://%s/user/me/paymentmethod/%d.json' % (
			self.request.host, paymentMethod['id']
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
		
		if paymentMethod['userID'] != user['id']:
			# The user is not authorized to see it
			error = {
				"domain": "application.resource.not_found",
				"display": "The specified payment method could not be found.",
				"debug": "no such resource"
			}
			self.set_status(404)
			self.renderJSON(error)
		
		self.renderJSON(paymentMethod.getPublicDict())
	
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
		
		paymentMethod['dateDeleted'] = datetime.now()
		paymentMethod.save()
		
		self.renderJSON([True])
