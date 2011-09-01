# WurkHappy Web Application Template
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.options as options
import tornado.web as web

from handlers import *
from tools.email import *
from tools.orm import *
from tools.amazonaws import *
import os
import os.path



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
			# (r'/profiles/?(.*)', profilehandlers.ProfilesHandler),
			# (r'/profile/?([^\./|^\.\\]+)?/?([^\./|^\.\\]+)?', profilehandlers.ProfileHandler),
			(r'/forgot_password', authhandlers.ForgotPasswordHandler),
			(r'/reset_password', authhandlers.ResetPasswordHandler),
			
			# (r'/user/([0-9]+)/preferences/?', users.PreferencesHandler),
			# (r'/user/([0-9]+)/preferences\.json', users.PreferencesJSONHandler),
			(r'/user/me/contacts.json', users.ContactsJSONHandler),
			(r'/user/me/account', accounts.AccountHandler),
			(r'/user/me/account/password.json', accounts.PasswordJSONHandler),
			(r'/user/me/account/personal.json', accounts.AccountJSONHandler),
			(r'/user/me/account/bank.json', accounts.BankJSONHandler),
			(r'/user/me/account/credit.json', accounts.CreditJSONHandler),
			
			(r'/user/me/password.json', authhandlers.PasswordJSONHandler),
			
			# (r'/project/([0-9]+)', projecthandlers.ProjectHandler),
			# (r'/project/?', projecthandlers.ProjectHandler),
			# (r'/invoice/([0-9]+)', invoicehandlers.InvoiceHandler),
			# (r'/invoice/?', invoicehandlers.InvoiceHandler),
			# (r'/line_item.json', invoicehandlers.LineItemHandler),
			# (r'/line_item/([0-9]+)\.json', invoicehandlers.LineItemHandler),
			
			(r'/agreements/with/(clients|vendors)/?', agreements.AgreementListHandler),
			(r'/agreement/([0-9]*)/?', agreements.AgreementHandler),
			(r'/agreement/new/?', agreements.AgreementHandler),
			
			(r'/agreement/([0-9]+)\.json', agreements.AgreementJSONHandler),
			(r'/agreement/([0-9]+)/status.json', agreements.AgreementStatusJSONHandler),
			(r'/agreement/new\.json', agreements.NewAgreementJSONHandler),
			
			(r'/file', files.FileHandler)
		]
		
		settings = {
			"xsrf_cookies": True,
			# Convert cookie_secret from unicode string to ascii string, so as not to break hashlib
			"cookie_secret": str(config['tornado']['cookie_secret']), 
			"login_url": "/login",
			"template_path": os.path.join(os.path.dirname(__file__), "templates"),
			"static_path": os.path.join(os.path.dirname(__file__), "static"),
			"debug": config['tornado']['debug']
		}
		
		web.Application.__init__(self, handlers, **settings)
		self.configuration = config
		
		Database.configure({
			"host": config['database']['host'],
			"user": config['database']['user'],
			"passwd": config['database']['passwd'],
			"db": config['database']['db']
		}, None)
		
		# AmazonS3.configure(config['amazonaws'])
		Email.configure(config['smtp'])


# -------------------------------------------------------------------
# Command-line Startup
# -------------------------------------------------------------------

if __name__ == "__main__":
	import yaml
	
	options.define("config", default="config.yaml", help="load configuration from file", type=str)
	options.define("port", default=None, help="listen port", type=int)
	options.define("address", default=None, help="listen address", type=str)
	options.define("debug", default=False, help="start in debug mode", type=bool)
	options.parse_command_line()
	
	workingDir = os.path.dirname(__file__)
	if workingDir:
		os.chdir(workingDir)
	
	conf = yaml.load(open(options.options.config, 'r'))
	conf['tornado']['debug'] = options.options.debug
	server = HTTPServer(Application(conf))
	
	port = options.options.port
	address = options.options.address
	
	if not port:
		port = conf['tornado']['port']
	
	if not address:
		address = conf['tornado']['address']

	server.listen(port, address)
	IOLoop.instance().start()
	
