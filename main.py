# WurkHappy Web Application Template
# Version 0.5
#
# Written by Brendan Berg
# Copyright WurkHappy, 2011 - 2012

import yaml

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options as options
import tornado.web as web

from controllers.handlers import *
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
			# Redirect as appropriate based on user state
			(r'/', root.RootHandler),
			
			(r'/account/create/?', accounts.AccountCreationHandler),
			(r'/account/setup/?', accounts.AccountSetupHandler),
			
			(r'/login', authentication.LoginHandler),
			(r'/login.json', authentication.LoginJSONHandler),
			(r'/logout', authentication.LogoutHandler),
			
			(r'/legal/terms/?', legal.TermsHandler),
			(r'/legal/privacy/?', legal.PrivacyHandler),
			# (r'/legal/dwolla/?', legal.DwollaHandler),
			
			(r'/user/([0-9]*)/?', users.ProfileHandler),
			(r'/user/me/profile/?', users.ProfileHandler),
			(r'/user/me/account/?', accounts.AccountHandler),
			
			# Password handler with instructions to request a reset email
			# and update the password with the token from the email.
			(r'/user/me/password/?', accounts.PasswordHandler),
			(r'/user/me/password/reset.json', accounts.PasswordRecoveryJSONHandler),
			
			# JSON handlers to update account information
			(r'/user/me/account\.json', accounts.AccountJSONHandler),
			(r'/user/me/connections/?', accounts.AccountConnectionHandler),
			(r'/user/me/password\.json', accounts.PasswordJSONHandler),
			
			(r'/user/me/paymentmethod/new\.json', accounts.NewPaymentMethodJSONHandler),
			(r'/user/me/paymentmethod/([0-9]+)\.json', accounts.PaymentMethodJSONHandler),
			
			# Wurk Happy contact directory for current user
			(r'/user/me/contacts\.json', users.ContactsJSONHandler),
			
			# Comet handler for site notifications
			(r'/user/me/notifications\.json', notifications.NotificationHandler),
			
			(r'/agreements/with/(clients|vendors)/?', agreements.AgreementListHandler),
			(r'/agreement/([0-9]*)/?', agreements.AgreementHandler),
			(r'/agreement/new/?', agreements.AgreementHandler),
			
			# JSON handlers to create & update agreements and change their state
			(r'/agreement/([0-9]+)\.json', agreements.AgreementJSONHandler),
			(r'/agreement/([0-9]+)/status\.json', agreements.AgreementStatusJSONHandler),
			(r'/agreement/([0-9]+)/(save|send|accept|decline|mark_complete|verify|dispute)\.json', agreements.AgreementActionJSONHandler),
			(r'/agreement/(save|send)\.json', agreements.NewAgreementJSONHandler),
			
			# JSON handler to initiate a new payment
			(r'/payment/new\.json', payments.PaymentHandler),
			
			(r'/agreement/request/?', requests.RequestAgreementHandler),
			(r'/agreement/request\.json', requests.RequestAgreementJSONHandler),
			
			# JSON handler to test server configuration
			(r'/test/http_server\.json', tests.HTTPServerTestHandler)
		]
		
		settings = {
			"xsrf_cookies": True,
			# Convert cookie_secret from unicode string to ascii string, so as not to break hashlib
			"cookie_secret": str(config['tornado']['cookie_secret']),
			"login_url": "/login",
			"template_path": os.path.join(os.path.dirname(__file__), "templates"),
			"static_path": os.path.join(os.path.dirname(__file__), "static"),
			"ui_modules": modules,
			"debug": config['tornado'].get('debug', False),
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
	
	xheaders = conf['tornado'].get('xheaders', False)
	
	server = HTTPServer(Application(conf), xheaders=xheaders)

	port = options.options.port
	address = options.options.address

	if not port:
		port = conf['tornado']['port']

	if not address:
		address = conf['tornado']['address']

	server.listen(port, address)
	IOLoop.instance().start()

