from base import *
from models.user import *
from helpers.verification import Verification

from datetime import datetime
import logging

class RootHandler(BaseHandler):
	def get(self):
		self.render('landing/index.html',
			title="Wurk Happy &ndash; Our platform gets you paid faster.")



class SignupHandler(BaseHandler):
	def get(self):
		self.set_status(405)
		self.redirect('/')
	
	def post(self):
		email = self.get_argument("email", None)
		
		if email.count('@') != 1:
			self.set_status(400)
			return
		
		(user, domain) = email.split('@', 1)
		
		import re
		
		r = re.compile(r'^[A-Za-z0-9!#$%&\'*+-\/=?^_`{|}~]+$')
		
		if not r.search(user):
			self.set_status(400)
			return
		
		r = re.compile(r'^([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$')
		
		if not r.search(domain):
			self.set_status(400)
			return
		
		user = User.retrieveByEmail(email)
		
		if not user:
			user = User()
			user.email = email
			user.confirmed = 0
			# user.invited = 0
			user.dateCreated = datetime.now()
			verifier = Verification()
			user.confirmationCode = verifier.code
			user.confirmationHash = verifier.hashDigest
			user.save()
		
		self.render('landing/thankyou.html',
			title="Wurk Happy &ndash; Our platform gets you paid faster.")
	
class SignupJSONHandler(BaseHandler):
	def get(self):
		self.set_status(405);
		self.redirect('/');
	
	def post(self):
		email = self.get_argument("email", None)
		
		if email.count('@') != 1:
			self.set_status(400)
			self.write('{"success":false,"message":"I\'m sorry, that didn\'t look like a proper email address. Could you please enter a valid email address?"}')
			return
		
		(user, domain) = email.split('@', 1)
		
		import re
		
		r = re.compile(r'^[A-Za-z0-9!#$%&\'*+-\/=?^_`{|}~]+$')
		
		if not r.search(user):
			self.set_status(400)
			self.write('{"success":false,"message":"I\'m sorry, that didn\'t look like a proper email address. Could you please enter a valid email address?"}')
			return
		
		r = re.compile(r'^([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$')
		
		if not r.search(domain):
			self.set_status(400)
			self.write('{"success":false,"message":"I\'m sorry, that didn\'t look like a proper email address. Could you please enter a valid email address?"}')
			return
		
		logging.info(email)
		user = User.retrieveByEmail(email)
		
		if not user:
			user = User()
			user.email = email
			user.confirmed = 0
			# user.invited = 0
			user.dateCreated = datetime.now()
			verifier = Verification()
			user.confirmationCode = verifier.code
			user.confirmationHash = verifier.hashDigest
			user.save()
		
		self.write('{"success":true}')
	

class AboutHandler(BaseHandler):
	def get(self):
		self.render('landing/about.html',
			title="Wurk Happy is in New York City.")



class JobsHandler(BaseHandler):
	def get(self):
		self.render('landing/jobs.html',
			title="Wurk Happy is hiring.")
	

