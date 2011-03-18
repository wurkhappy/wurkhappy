# WurkHappy Web Application Template
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options as options
import tornado.web as web
from datetime import datetime

from tools.orm import *
import models
from controllers import Verification, Validation

# -------------------------------------------------------------------
# Application main
# 
# (settings and handler dispatch configuration)
# -------------------------------------------------------------------

class Application(web.Application):
	def __init__(self, config):
		handlers = [
			(r'/', RootHandler),
			(r'/signup', SignupHandler),
			(r'/login', LoginHandler),
			(r'/profile', ProfileHandler),
		]
		
		settings = {
			"xsrf_cookies": True,
			#convert cookie_secret from unicode string to ascii string, so as not to break hashlib
			"cookie_secret": str(config['tornado']['cookie_secret']), 
			"login_url": "/login",
			"template_path": "templates"
		}
		
		web.Application.__init__(self, handlers, **settings)
		
		Database.configure({
			"host": config['database']['host'],
			"user": config['database']['user'],
			"passwd": config['database']['passwd'],
			"db": config['database']['db']
		}, None)
	


# -------------------------------------------------------------------
# Handler base classes and mix-ins
# -------------------------------------------------------------------

class Authenticated(object):
	def get_current_user(self):
		userID = self.get_secure_cookie("user_id")
		return userID and models.User.retrieveByID(userID)
	
	def _is_superuser(self):
		pass
	

class BaseHandler(web.RequestHandler):
	def authenticated(self, method):
		pass
	
	def superuser(self, method):
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
		flash = {}
		err = self.get_argument("err", None)
		if err:
			flash["error"] = self.ERR[err]
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
	def get(self):
		self.render("user/login.html", title="Login")
	
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
		self.write("userID is %s" % user.id)
		
		# if not user or user.id != self.get_argument("user_id"):
		# 			self.set_error(404)
		# 			self.write("Not found")
		# 			return
		# 		
		# 		user = models.User.retrieveByID(userID)
		# 		
		# 		if not user:
		# 			self.set_error(404)
		# 			self.write("Not found")
		# 			return
		# 		
		# 		profile = models.Profile.retrieveByUserID(userID)
		# 		
		# 		self.write("%s %s\n" % (user.firstName, user.lastName))
		# 		self.write("%s\n" % user.email)
		# 		self.write("%s\n" % profile.bio)
		


# -------------------------------------------------------------------
# Command-line Startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	options.define("port", default=8888, help="run on the given port", type=int)
	options.define("config", default="config.json", help="load configuration from file", type=str)
	options.parse_command_line()
	
	conf = json.load(open(options.options.config, 'r+'))
	server = HTTPServer(Application(conf))
	server.listen(options.options.port)
	IOLoop.instance().start()
	
