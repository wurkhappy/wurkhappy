from base import *
from helpers.verification import Verification
from helpers.validation import Validation
from helpers import fmt
from models.user import User
from models.forgotpassword import ForgotPassword
from tools.email import *
from datetime import datetime, timedelta


# -------------------------------------------------------------------
# Signup
# -------------------------------------------------------------------

class SignupHandler(BaseHandler):
	ERR = 	{	
			"email_exists":"That email already exists. Please use a different email.",
			"email_invalid":"That email address is invalid. Please use a valid email address."
			}

	def get(self):
		flash = {"error": self.parseErrors()}
		self.render("user/signup.html", title="Sign Up", flash=flash, logged_in_user=self.current_user)

	def post(self):
		email = self.get_argument("email")

		# Validate format of email address
		if not Validation.validateEmail(email):
			self.redirect("/signup?err=email_invalid")

		# Check whether user exists already
		user = User.retrieveByEmail(email)

		# User wasn't found, so begin sign up process
		if not user:
			user = User()
			user.email = email
			user.confirmed = 0
			user.dateCreated = datetime.now()
			verifier = Verification()
			user.confirmationCode = verifier.code
			user.confirmationHash = verifier.hashDigest
			user.save()
			self.set_secure_cookie("user_id", str(user.id))
			self.redirect('/profiles/new')
		else:
			# User exists, redirect with error
			self.redirect("/signup?err=email_exists")

# -------------------------------------------------------------------
# Login
# -------------------------------------------------------------------

class LoginHandler(BaseHandler):
	ERR = 	{	
			"auth_invalid":"That email / password combination is incorrect. Please try again or click \"Forgot Password\"."
			}
	def get(self):
		flash = {"error": self.parseErrors()}
		from_reset_password = self.get_argument("rp", None)
		if from_reset_password:
			flash["error"] = ["Your password was reset successfully."]
		self.render("user/login.html", title="Sign In", flash=flash, logged_in_user=self.current_user)

	def post(self):
		email = self.get_argument("email")
		password = self.get_argument("password")
		user = User.retrieveByEmail(email)
		
		if not user or not Verification.check_password(user.password, str(password)):
			# User wasn't found, or password is wrong, redirect to login with error
			self.redirect("/login?err=auth_invalid")
		else:
 			profile = user.getProfile()
			self.set_secure_cookie("user_id", str(user.id))
			self.redirect('/profile/'+profile.urlStub)
			
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
			forgotPassword.userID = user.id
			forgotPassword.code = code
			forgotPassword.validUntil = datetime.now() + timedelta(hours=24)
			forgotPassword.active = 1
			forgotPassword.save()
			# send an email to the user containing a link to reset password with the code
			link = "http://"+self.request.host+"/reset_password?code="+code
			msg = """\
			To reset your password, click on this link and enter a new password. (The link is only valid for the next 24 hours.)
			"""+link
			Email.sendFromApp(user.email, 'Reset Password', msg)
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
		elif not self.current_user and (forgotPassword.validUntil < datetime.now() or forgotPassword.active == False):
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
				user = User.retrieveByUserID(forgotPassword.userID)
			user.password = Verification.hash_password(str(password))
			user.save()
			flash = {"error": "Your password was reset successfully."}
			if forgotPassword:
				forgotPassword.active = 0
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
			
			if not user or not Verification.check_password(user.password, str(args['currentPassword'])):
				# User wasn't found, or password is wrong, display error
				#TODO: Exponential back-off when user enters incorrect password.
				#TODO: Flag accounds if passwords change too often.
				error = {
					"domain": "web.request",
					"debug": "please validate authentication credentials"
				}
				self.set_status(401)
				self.write(json.dumps(error))
			else:
				user.password = Verification.hash_password(str(args['newPassword']))
				user.save()
				self.write(json.dumps({"success": True}))
