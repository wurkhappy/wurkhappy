# WurkHappy Administration Application
# Version 0.2
#
# Written by Brendan Berg
# Copyright WurkHappy, 2012

import yaml

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options as options
import tornado.web as web

from controllers.handlers.admin import *
from controllers.email import Email
from controllers.orm import Database
from controllers.amazonaws import AmazonS3
from controllers.beanstalk import Beanstalk

import os
import os.path

from controllers.modules import modules

# -------------------------------------------------------------------
# Application main
#
# (settings and handler dispatch configuration)
# -------------------------------------------------------------------

class Application(web.Application):
	def __init__(self, config):
		handlers = [
			(r'/', root.RootHandler),
			(r'/login', auth.LoginHandler),
			(r'/logout', auth.LogoutHandler),
			
			(r'/users/?', users.UserListHandler),
			(r'/user/([0-9]+)/?', users.UserDetailHandler),
			(r'/user/([0-9]+)\.json', users.UserActionJSONHandler),
			
			(r'/agreements/?', agreements.AgreementListHandler),
			(r'/agreement/([0-9]+)/?', agreements.AgreementListHandler),
			
			(r'/transactions/?', transactions.TransactionListHandler),
			(r'/transaction/([0-9]+)/?', transactions.TransactionDetailHandler)
		]

		settings = {
			"xsrf_cookies": True,
			# Convert cookie_secret from unicode string to ascii string, so as not to break hashlib
			"cookie_secret": str(config['admin']['cookie_secret']),
			"login_url": "/login",
			"template_path": os.path.join(os.path.dirname(__file__), "templates/admin"),
			"static_path": os.path.join(os.path.dirname(__file__), "static"),
			"ui_modules": modules,
			"debug": config['admin'].get('debug', False),
			"xheaders": config['admin'].get('xheaders', False)
		}

		web.Application.__init__(self, handlers, **settings)
		self.configuration = config

		Database.configure({
			"host": config['database']['host'],
			"user": config['database']['user'],
			"passwd": config['database']['passwd'],
			"db": config['database']['db']
		}, None)

		Beanstalk.configure(config['beanstalk'])
		AmazonS3.configure(config['amazonaws'])
		Email.configure(config['smtp'])


# -------------------------------------------------------------------
# Command-line Startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	options.define("config", default="config.yaml", help="load configuration from file", type=str)
	options.define("port", default=None, help="listen port", type=int)
	options.define("address", default=None, help="listen address", type=str)
	options.define("debug", default=None, help="start in debug mode", type=bool)
	options.parse_command_line()

	workingDir = os.path.dirname(__file__)
	if workingDir:
		os.chdir(workingDir)

	conf = yaml.load(open(options.options.config, 'r'))

	# Override debug setting with command line flag, if set
	if options.options.debug:
		conf['tornado']['debug'] = options.options.debug

	server = HTTPServer(Application(conf))

	port = options.options.port
	address = options.options.address

	if not port:
		port = conf['admin']['port']

	if not address:
		address = conf['admin']['address']

	server.listen(port, address)
	IOLoop.instance().start()

