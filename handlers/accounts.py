from __future__ import division

from base import *
from models.user import User, UserPrefs

from helpers import fmt

import json
import logging
import os
import uuid
from hashlib import sha1
import Image, ImageOps
from StringIO import StringIO
from tools.base import Base16, Base58
from tools.amazonaws import AmazonS3
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
			'id': user.id,
			'firstName': user.firstName,
			'lastName': user.lastName,
			'fullName': user.getFullName(),
			'email': user.email,
			'telephone': user.telephone or '',
			'profileURL': [
				user.profileSmallURL or '#',
				user.profileLargeURL or '#'
			]
		}
		
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
		
		#TODO
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
		
		#TODO: This needs refactoring
		if 'profilePhoto' in self.request.files:
			logging.warn('Got profile photo!')
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
		self.write(json.dumps({"success": True}))



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
					('old_password', fmt.Enforce(str)),
					('new_password', fmt.Enforce(str)),
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
# BankJSONHandler
# -------------------------------------------------------------------

class BankJSONHandler(Authenticated, BaseHandler):

	@web.authenticated
	def post(self):
		print 'BankJSONHandler'

# -------------------------------------------------------------------
# CreditJSONHandler
# -------------------------------------------------------------------

class CreditJSONHandler(Authenticated, BaseHandler):

	@web.authenticated
	def post(self):
		print 'CreditJSONHandler'
