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
			
			# self.redirect("/signup?err=email_invalid")
			return
		
		# Check whether user exists already
		user = User.retrieveByEmail(args['email'])
		
		# User wasn't found, so begin sign up process
		if not user:
			user = User()
			user['email'] = args['email']
			# user['confirmed'] = 0
			user['dateCreated'] = datetime.now()
			verifier = Verification()
			user['confirmationCode'] = verifier.code
			user['confirmationHash'] = verifier.hashDigest
			user.setPasswordHash(args['password'])
			user.save()
			
			# @todo: This should be better. Static value in config file...
			# user.profileSmallURL = self.application.config['application']['profileURLFormat'].format({"id": user.id % 5, "size": "s"})
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
			# self.redirect("/signup?err=email_exists")



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
# Forgot Password
# -------------------------------------------------------------------
		
class ForgotPasswordHandler(BaseHandler):
	ERR = 	{	
			"email_does_not_exist":"That email does not exist in our system. Please use a different email."
			}

	def get(self):
		flash = {"error": self.parseErrors()}
		self.render("user/forgot_password.html", title="Forgot Password", flash=flash, logged_in_user=self.current_user)

	def post(self):
		# Check whether user exists 
		user = User.retrieveByEmail(self.get_argument("email"))

		# User wasn't found, so redirect with error
		if not user:
			flash = {"error": [self.ERR["email_does_not_exist"]]}
			self.render("user/forgot_password.html", title="Forgot Password", flash=flash, logged_in_user=self.current_user)
		else: # user exists
			# generate a code
			verifier = Verification()
			code = verifier.hashDigest
			# build rest of forgot password model
			forgotPassword = ForgotPassword()
			forgotPassword['userID'] = user['id']
			forgotPassword['code'] = code
			forgotPassword['validUntil'] = datetime.now() + timedelta(hours=24)
			forgotPassword['active'] = 1
			forgotPassword.save()
			# send an email to the user containing a link to reset password with the code
			link = "http://"+self.request.host+"/reset_password?code="+code
			msg = """\
			To reset your password, click on this link and enter a new password. (The link is only valid for the next 24 hours.)
			"""+link
			Email.sendFromApp(user['email'], 'Reset Password', msg)
			# render template to confirm
			self.render("user/forgot_password_confirm.html", title="Forgot Password", logged_in_user=self.current_user)

# -------------------------------------------------------------------
# Reset Password
# -------------------------------------------------------------------


class ResetPasswordHandler(Authenticated, BaseHandler):
	ERR = 	{	
			"passwords_do_not_match":"The passwords you entered do not match, please try again."
			}

	def get(self):
		flash = {"error": self.parseErrors()}
		code = self.get_argument("code", '')
		flash["code"] = code
		forgotPassword = ForgotPassword.retrieveByCode(code)
		if not self.current_user and not forgotPassword:
			self.set_status(403)
			self.write("Forbidden")
			return
		elif not self.current_user and (forgotPassword['validUntil'] < datetime.now() or forgotPassword['active'] == False):
			self.set_status(403)
			self.write("Forbidden")
			return
		else:
			self.render("user/reset_password.html", title="Reset Password", flash=flash, logged_in_user=self.current_user)

	def post(self):
		password = self.get_argument("password")
		cpassword = self.get_argument("confirm_password")
		code = self.get_argument("code", '')
		forgotPassword = ForgotPassword.retrieveByCode(code)
		if not self.current_user and not forgotPassword:
			self.set_status(403)
			self.write("Forbidden")
			return
		elif password != cpassword:
			flash = {"error":[self.ERR["passwords_do_not_match"]], "code":code}
			self.render("user/reset_password.html", title="Reset Password", flash=flash, logged_in_user=self.current_user)
		else:
			user = None
			if not forgotPassword:
				user = self.current_user
			else:
				user = User.retrieveByUserID(forgotPassword['userID'])
			user['password'] = Verification.hash_password(str(password))
			user.save()
			flash = {"error": "Your password was reset successfully."}
			if forgotPassword:
				forgotPassword['active'] = 0
				forgotPassword.save()
			if self.current_user:
				# if user is already logged in, redirect to edit profile page
			 	self.redirect("/profile/"+self.current_user.getProfile().urlStub+"/edit?rp=true")
			else:
				self.redirect("/login?rp=true")


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
