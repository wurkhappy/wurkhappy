# WurkHappy Web Application Template
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options as options
import tornado.web as web

from tools.orm import *
import models

# -------------------------------------------------------------------
# Application main
# 
# (settings and handler dispatch configuration)
# -------------------------------------------------------------------

class Application(web.Application):
	def __init__(self, config):
		handlers = [
			(r'/', RootHandler)
		]
		
		settings = {
			"xsrf_cookies": True,
			"cookie_secret": config['tornado']['cookie_secret']
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
	def _get_current_user(self):
		userID = self.get_secure_cookie("user_id")
		return userID and models.User.retrieveByID(userID)
	


# -------------------------------------------------------------------
# Handler classes
# -------------------------------------------------------------------

class RootHandler(web.RequestHandler):
	def get(self):
		self.write("Good morning, gentlemen!")
	

