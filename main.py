# WurkHappy Web Application Template
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options as options
import tornado.web as web

from handler import *
from controllers import *
from tools.email import *
from tools.orm import *

# -------------------------------------------------------------------
# Application main
# 
# (settings and handler dispatch configuration)
# -------------------------------------------------------------------

class Application(web.Application):
	def __init__(self, config):
		handlers = [
			(r'/', root.RootHandler),
			(r'/signup', authhandlers.SignupHandler),
			(r'/login', authhandlers.LoginHandler),
			(r'/logout', authhandlers.LogoutHandler),
			(r'/profiles/?(.*)', profilehandlers.ProfilesHandler),
			(r'/profile/?([^\./|^\.\\]+)?/?([^\./|^\.\\]+)?', profilehandlers.ProfileHandler),
			(r'/forgot_password', authhandlers.ForgotPasswordHandler),
			(r'/reset_password', authhandlers.ResetPasswordHandler)
		]
		
		settings = {
			"xsrf_cookies": True,
			#convert cookie_secret from unicode string to ascii string, so as not to break hashlib
			"cookie_secret": str(config['tornado']['cookie_secret']), 
			"login_url": "/login",
			"template_path": "templates",
			"static_path": "static"
		}
		
		web.Application.__init__(self, handlers, **settings)
		
		Database.configure({
			"host": config['database']['host'],
			"user": config['database']['user'],
			"passwd": config['database']['passwd'],
			"db": config['database']['db']
		}, None)
		
		Email.configure(config['smtp'])


# -------------------------------------------------------------------
# Command-line Startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	options.define("config", default="config.json", help="load configuration from file", type=str)
	options.parse_command_line()
	
	conf = json.load(open(options.options.config, 'r+'))
	server = HTTPServer(Application(conf))
	server.listen(conf['tornado']['port'], conf['tornado']['address'])
	IOLoop.instance().start()
	
