# WurkHappy Helpers
# Version 0.1
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2011

import tornado.web as web
from tools.orm import *
from helpers import *
import models
import handlers 

from datetime import datetime

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
		self.render("user/signup.html", title="Sign Up", flash=flash)

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
			self.redirect('/profile')
		else:
			# User exists, redirect with error
			self.redirect("/signup?err=email_exists")


class LoginHandler(BaseHandler):
	ERR = 	{	
			"auth_invalid":"That email / password combination is incorrect. Please try again or click \"Forgot Password\"."
			}
	def get(self):
		flash = {"error": self.parseErrors()}
		self.render("user/login.html", title="Login", flash=flash)

	def post(self):
		email = self.get_argument("email")
		user = models.User.retrieveByEmail(email)
		if not user:
			# User wasn't found, redirect to login with error
			pass
		#else: 
		self.set_secure_cookie("user_id", str(user.id))
		self.redirect('/profile')


class ProfileHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		user = self.current_user

		if not user:
			self.set_error(404)
			self.write("Not found")
			return
		
		profile = models.Profile.retrieveByUserID(user.id)
		if not profile or self.get_argument("edit", None) == "y":
			# render edit template
			self.render("user/edit_profile.html", title="Edit Profile", user=user)
		else:
			# show profile
			self.render("user/show_profile.html", title="Profile", user=user, profile=profile)
			
	@web.authenticated
	def post(self):
		user = self.current_user
		
		# Validations
		# TODO
		
		# Retrieve profile for logged in user
		profile = models.Profile.retrieveByUserID(user.id)
		
		if not profile:
			# No profile exists yet, so create one and set its userID to the current user
			profile = models.Profile()
			profile.userID = user.id

		# Update profile
		profile.bio = self.get_argument("bio")
		profile.save()
		self.redirect('/profile')
