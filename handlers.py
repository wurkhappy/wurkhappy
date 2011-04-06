# WurkHappy Helpers
# Version 0.1
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2011

import tornado.web as web
from tools.orm import *
import models
import handlers 
from controllers import Verification, Validation
from tools.email import *
from datetime import datetime, timedelta
import re

# -------------------------------------------------------------------
# Handler Base Class and Mixins
# -------------------------------------------------------------------

class BaseHandler(web.RequestHandler):
	def authenticated(self, method):
		pass
	
	def superuser(self, method):
		pass
		
	def parseErrors(self):
		err = self.get_argument("err", None)
		if err:
			err = err.split('-')
			return [self.ERR.get(e) for e in err]
		else:
			return None


class Authenticated(object):
	def get_current_user(self):
		userID = self.get_secure_cookie("user_id")
		return userID and models.User.retrieveByID(userID)

	def _is_superuser(self):
		pass
		
# -------------------------------------------------------------------
# Handler classes
# -------------------------------------------------------------------

class RootHandler(BaseHandler):
	def get(self):
		self.write("How are you gentlemen!")


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
		user = models.User.retrieveByEmail(email)

		# User wasn't found, so begin sign up process
		if not user:
			user = models.User()
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
		user = models.User.retrieveByEmail(email)
		profile = models.Profile.retrieveByUserID(user.id)
		if not user or not Verification.check_password(user.password, str(password)):
			# User wasn't found, or password is wrong, redirect to login with error
			self.redirect("/login?err=auth_invalid")
		else:
 			self.set_secure_cookie("user_id", str(user.id))
			self.redirect('/profile/'+profile.urlStub)
			
class LogoutHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		self.clear_cookie("user_id")
		self.redirect('/login')
	
	@web.authenticated
	def post(self):
		self.set_status(404)
		self.write("Not found")

class ProfilesHandler(Authenticated, BaseHandler):
	def get(self, action):
		if action == "new":
			user = self.current_user
			
			if not user:
				self.set_status(403)
				self.write("Forbidden")
				return
			else:
				# check to see whether user already has a profile
			 	profile = models.Profile.retrieveByUserID(user.id)
				if profile:
					# if so, redirect to the edit profile page
					self.redirect("/profile/"+profile.urlStub+"/edit")
				else:
					# otherwise, create a new profile
					self.render("user/edit_profile.html", title="Create a Profile", user=user, profile=profile, logged_in_user=user)
		else:
			self.write('index')
			
	def post(self):
		pass

class ProfileHandler(Authenticated, BaseHandler):
	ERR = 	{	
			"name_missing":"All name fields are required."
			}
	def get(self, stub, action):	
		
		# retrieve profile from db based on url stub
		profile = models.Profile.retrieveByUrlStub(stub)
		
		# if stub doesn't exist, return 404 page
		if not profile:
			self.set_status(404)
			self.write("Not found")
			return
		
		else:
			user = models.User.retrieveByUserID(profile.userID)
			# if no action was passed, show profile	
			if not action:		
				self.render("user/show_profile.html", title="Profile", user=user, profile=profile, logged_in_user = self.current_user)
				
			# else if action is edit, make sure user is logged in and the logged in user matches the profile, if so render edit page
			elif action == "edit":
				flash = {"error": self.parseErrors()}
				from_reset_password = self.get_argument("rp", None)
				if from_reset_password:
					flash["error"] = ["Your password was reset successfully."]
				logged_in_user = self.current_user
				if not logged_in_user or logged_in_user.id != profile.userID:
					self.set_status(403)
					self.write("Forbidden")
					return
				self.render("user/edit_profile.html", title="Edit Profile", user=user, profile=profile, logged_in_user=self.current_user, flash=flash)
			
	@web.authenticated
	def post(self, *args):
		user = self.current_user
		
		if not user:
			self.set_status(404)
			self.write("Not found")
			return
		
		# Validations
		# need to make sure user entered a required profile name and other req'd fields!!
		errs = ""
		if not self.get_argument("name", None) or not self.get_argument("firstName", None) or not self.get_argument("lastName", None):
			errs += "name_missing"
		if errs != "":
			self.redirect('/profile/'+user.getProfile().urlStub+"/edit?err="+errs)
				
		# Set user fields
		
		user.firstName = self.get_argument("firstName")
		user.lastName = self.get_argument("lastName")
		
		if self.get_argument('password', None):
			user.password = Verification.hash_password(str(self.get_argument("password")))
		
		# Retrieve profile for logged in user
		profile = user.getProfile()
		
		if not profile:
			# No profile exists yet, so create one and set its userID to the current user
			profile = models.Profile()
			profile.userID = user.id

		# Update profile
		profile.bio = self.get_argument("bio")
		profile.name = self.get_argument("name")
		profile.urlStub = re.sub(r'[^\w^d]', r'-', profile.name.lower())
			
		user.save()
		sprofile.save()
		
		self.redirect('/profile/'+profile.urlStub)

class ForgotPasswordHandler(BaseHandler):
	ERR = 	{	
			"email_does_not_exist":"That email does not exist in our system. Please use a different email."
			}

	def get(self):
		flash = {"error": self.parseErrors()}
		self.render("user/forgot_password.html", title="Forgot Password", flash=flash, logged_in_user=self.current_user)
		
	def post(self):
		# Check whether user exists 
		user = models.User.retrieveByEmail(self.get_argument("email"))

		# User wasn't found, so redirect with error
		if not user:
			flash = {"error": [self.ERR["email_does_not_exist"]]}
			self.render("user/forgot_password.html", title="Forgot Password", flash=flash, logged_in_user=self.current_user)
		else: # user exists
			# generate a code
			verifier = Verification()
			code = verifier.hashDigest
			# build rest of forgot password model
			forgotPassword = models.ForgotPassword()
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
			
class ResetPasswordHandler(Authenticated, BaseHandler):
	ERR = 	{	
			"passwords_do_not_match":"The passwords you entered do not match, please try again."
			}

	def get(self):
		flash = {"error": self.parseErrors()}
		code = self.get_argument("code", '')
		flash["code"] = code
		forgotPassword = models.ForgotPassword.retrieveByCode(code)
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
		forgotPassword = models.ForgotPassword.retrieveByCode(code)
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
				user = models.User.retrieveByUserID(forgotPassword.userID)
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