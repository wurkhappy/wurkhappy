# WurkHappy Web Application Template
# Version 0.2
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options as options
import tornado.web as web

from controllers.handlers import landing
# from controllers.email import *
from controllers.orm import *

import os



# -------------------------------------------------------------------
# Application main
# 
# (settings and handler dispatch configuration)
# -------------------------------------------------------------------

class Application(web.Application):
	def __init__(self, config):
		handlers = [
			(r'/', landing.RootHandler),
			(r'/signup', landing.SignupHandler),
			(r'/signup.json', landing.SignupJSONHandler),
			(r'/about/?', landing.AboutHandler),
			(r'/about/(\w+)/?', landing.AboutPersonHandler),
			(r'/legal/(\w+)/?', landing.LegalHandler),
			(r'/jobs/?', landing.JobsHandler),
			(r'/techstars/?', landing.TechstarsHandler),
		]
		
		settings = {
			"xsrf_cookies": True,
			# Convert cookie_secret from unicode string to ascii string, so as not to break hashlib
			"cookie_secret": str(config['tornado']['cookie_secret']), 
			"login_url": "/login",
			"template_path": "templates",
			"static_path": "static",
			"debug": config['debug']
		}
		
		web.Application.__init__(self, handlers, **settings)
		self.configuration = config
		
		Database.configure({
			"host": config['database']['host'],
			"user": config['database']['user'],
			"passwd": config['database']['passwd'],
			"db": config['database']['db']
		}, None)
		
		# Email.configure(config['smtp'])


# -------------------------------------------------------------------
# Command-line Startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	try:
		import json
	except:
		import simplejson as json
	
	options.define("config", default="config.json", help="load configuration from file", type=str)
	options.define("port", default=None, help="listen port", type=int)
	options.define("address", default=None, help="listen address", type=str)
	options.define("debug", default=False, help="debug mode", type=bool)
	options.parse_command_line()
	
	workingDir = os.path.dirname(__file__)
	if workingDir:
		os.chdir(workingDir)
	
	conf = json.load(open(options.options.config, 'r'))
	conf['debug'] = options.options.debug
	server = HTTPServer(Application(conf))
	
	port = options.options.port
	address = options.options.address
	
	if not port:
		port = conf['tornado']['port']
	
	if not address:
		address = conf['tornado']['address']

	server.listen(port, address)
	IOLoop.instance().start()
	
