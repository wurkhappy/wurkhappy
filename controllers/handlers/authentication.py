from base import *
from controllers.verification import Verification
from controllers import fmt
from models.user import User
from models.forgotpassword import ForgotPassword
from controllers.email import *
from datetime import datetime, timedelta
import logging



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

class LoginJSONHandler(BaseHandler):
	'''Login handler for AJAX-style JSON requests. Responds to POST requests
	with the same verification behavior as the LoginHandler. Sets a secure
	cookie and returns the current user's public dict if successful.'''
	
	def post(self):
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('email', fmt.Email()),
					('password', fmt.Enforce(str))
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			logging.warn(e.message)
			
			error = {
				"domain": "authentication",
				"display": (
					"I'm sorry, that didn't look like a proper email "
					"address. Could you please enter a valid email address?"
				),
				"debug": "'email' parameter must be well-formed"
			}
			
			self.set_status(400)
			self.renderJSON(error)
			return
		
		user = User.retrieveByEmail(args['email'])
		
		if not user or not user.passwordIsValid(args['password']):
			# User wasn't found, or password is wrong, render login with error
			error = {
				"domain": "authentication",
				"display": (
					"I'm sorry, the email and password combination you "
					"entered doesn't match any of our records. Please check "
					"for typos and make sure caps lock is turned off when "
					"entering your password."
				),
				"debug": "incorrect email or password"
			}
			
			self.set_status(401)
			self.renderJSON(error)
		
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
			success = {
				"user": user.getPublicDict()
			}
			self.set_secure_cookie("user_id", str(user['id']), httponly=True)
			self.renderJSON(success)



# -------------------------------------------------------------------
# Logout 
# -------------------------------------------------------------------

class LogoutHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		self.clear_cookie("user_id")
		self.redirect('/login')

	# I'm not sure why the POST method was stubbed out to return 404.
	# I've commented it out and if it breaks anything, I'll add it back.
	
	# @web.authenticated
	# def post(self):
	# 	self.set_status(404)
	# 	self.write("Not found")
