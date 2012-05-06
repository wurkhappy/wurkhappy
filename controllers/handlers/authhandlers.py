from base import *
from controllers.verification import Verification
from controllers import fmt
from models.user import User
from models.forgotpassword import ForgotPassword
from controllers.email import *
from datetime import datetime, timedelta
import logging

# -------------------------------------------------------------------
# Signup
# -------------------------------------------------------------------

class SignupHandler(BaseHandler):
	
	def get(self):
		self.render("user/signup.html", title="Sign Up", error=None)

	def post(self):
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('email', fmt.Email()),
					('password', fmt.Enforce(str))
					# @todo: Should have a password plaintext formatter to
					# enforce well-formed passwords.
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			logging.warn(e.message)
			
			if e.body_content.find("'password' parameter is required") != -1:
				# We caught an exception because the password was missing
				error = {
					"domain": "authentication",
					"display": (
						"I'm sorry, you must choose a password to continue. "
						"Please pick a password that is easy for you to "
						"remember, but hard for others to guess."
					),
					"debug": "'password' parameter is required"
				}
			else:
				error = {
					"domain": "authentication",
					"display": (
						"I'm sorry, that didn't look like a proper email "
						"address. Could you please enter a valid email address?"
					),
					"debug": "'email' parameter must be well-formed"
				}
			
			self.set_status(e.status_code)
			self.render("user/signup.html", title="Sign Up for Wurk Happy", error=error)
			return
		
		# Check whether user exists already
		user = User.retrieveByEmail(args['email'])
		
		# User wasn't found, so begin sign up process
		if not user:
			user = User()
			user['email'] = args['email']
			user['dateCreated'] = datetime.now()
			# verifier = Verification()
			# user.setConfirmationHash(verifier.code)
			user.setPasswordHash(args['password'])
			user.save()
			
			# @todo: This should be better. Static value in config file...
			# user.profileSmallURL = self.application.configuration['application']['profileURLFormat'].format({"id": user.id % 5, "size": "s"})
			# "http://media.wurkhappy.com/images/profile{id}_{size}.jpg"
			user['profileSmallURL'] = "http://media.wurkhappy.com/images/profile%d_s.jpg" % (user['id'] % 5)
			user.save()
			
			self.set_secure_cookie("user_id", str(user['id']), httponly=True)
			self.redirect('/user/me/account')
		else:
			# User exists, render with error
			error = {
				"domain": "authentication",
				"display": (
					"I'm sorry, that email already exists. Did you mean to "
					"log in instead?"
				),
				"debug": "specified email address is already registered"
			}
			
			self.set_status(400)
			self.render("user/signup.html", title="Sign Up for Wurk Happy", error=error)



# -------------------------------------------------------------------
# Login
# -------------------------------------------------------------------

class LoginHandler(BaseHandler):
	def get(self):
		self.render("user/login.html", title="Sign In to Wurk Happy", error=None)
	
	
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
			self.render("user/login.html", title="Sign In to Wurk Happy", error=error)
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
			self.render("user/login.html", title="Sign In to Wurk Happy", error=error)
		else:
			self.set_secure_cookie("user_id", str(user['id']), httponly=True)
			self.redirect('/user/me/account') #TODO: Should go to dashboard...



# -------------------------------------------------------------------
# Logout 
# -------------------------------------------------------------------

class LogoutHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		self.clear_cookie("user_id")
		self.redirect('/login')

	@web.authenticated
	def post(self):
		self.set_status(404)
		self.write("Not found")
		


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
			logging.warn(e.__dict__)
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		if not (user and user.passwordIsValid(args['currentPassword'])):
			# User wasn't found, or password is wrong, display error
			# @todo: Exponential back-off when user enters incorrect password.
			# @todo: Flag accounds if passwords change too often.
			error = {
				"domain": "web.request",
				"debug": "please validate authentication credentials"
			}
			self.set_status(401)
			self.renderJSON(error)
		else:
			user.setPasswordHash(args['newPassword'])# = Verification.hash_password(str(args['new_password']))
			user.save()
			self.write(json.dumps({"success": True}))
