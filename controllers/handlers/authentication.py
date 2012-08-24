from base import *
from controllers.verification import Verification
from controllers import fmt
from models.user import User
from controllers.email import *
from datetime import datetime, timedelta
import logging
from urlparse import urlparse
from urllib import unquote



# -------------------------------------------------------------------
# Login
# -------------------------------------------------------------------

class LoginHandler(BaseHandler):
	def get(self):
		data = { "_xsrf": self.xsrf_token }
		self.render("auth/login.html", title="Sign In to Wurk Happy", data=data)



# -------------------------------------------------------------------
# JSON Login Handler
# -------------------------------------------------------------------

class LoginJSONHandler(Authenticated, JSONBaseHandler):
	'''Login handler for AJAX-style JSON requests. Responds to POST requests
	with the same verification behavior as the LoginHandler. Sets a secure
	cookie and returns the current user's public dict if successful.'''
	
	def post(self):
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('email', fmt.Email()),
					('user_id', fmt.PositiveInteger())
				],
				required=[
					('password', fmt.Enforce(str))
				]
			)
		except fmt.HTTPErrorBetter as e:
			self.error_description = {
				"domain": "authentication",
				"display": (
					"I'm sorry, that didn't look like a proper email "
					"address. Could you please enter a valid email address?"
				),
				"debug": "'email' parameter must be well-formed"
			}
			raise HTTPError(400, 'Missing or malformed login parameters')
		
		if args['email']:
			user = User.retrieveByEmail(args['email'])
		else:
			user = User.retrieveByID(args['user_id'])
		
		if not user or not user.passwordIsValid(args['password']):
			# User wasn't found, or password is wrong, render login with error
			self.error_description = {
				"domain": "authentication",
				"display": (
					"I'm sorry, the email and password combination you "
					"entered doesn't match any of our records. Please check "
					"for typos and make sure caps lock is turned off when "
					"entering your password."
				),
				"debug": "incorrect email or password"
			}
			raise(401, 'incorrect email or password')
		
		# TODO: We should figure out how to enforce that all users who log in
		# are active users without preventing new users from providing their
		# passwords.
		
		# userState = user.getCurrentState()
		# 
		# if not isinstance(userState, ActiveUserState):
		# 	# User has not been activated or is locked
		# 	error = {
		# 		"domain": 'authentication',
		# 		'display': (
		# 			'The account you are trying to access has not been set up '
		# 			'yet. Please check your email for instructions to activate '
		# 			'your account.'
		# 		),
		# 		'debug': 'non-active user'
		# 	}
		# 	
		# 	self.set_status(401)
		# 	self.renderJSON(error)
		else:
			queryString = urlparse(self.request.headers.get('Referer', '')).query
			
			success = {
				"user": user.getPublicDict()
			}
			
			if queryString:
				next = {pair.split('=')[0]: pair.split('=')[1] for pair in queryString.split('&')}.get('next', '/')
				self.set_header('Location', '{0}://{1}{2}'.format(
					self.request.protocol,
					self.application.configuration['wurkhappy']['hostname'],
					unquote(next)
				))
			
			self.setAuthCookiesForUser(user, mode='cookie')
			self.renderJSON(success)



# -------------------------------------------------------------------
# Logout 
# -------------------------------------------------------------------

class LogoutHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		self.clear_cookie("user_id")
		self.clear_cookie('auth')
		self.clear_cookie('auth_timestamp')
		self.redirect('/login')
