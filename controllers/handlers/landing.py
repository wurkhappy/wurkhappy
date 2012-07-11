from base import BaseHandler
from models.user import User, UserPrefs
from controllers import fmt
# from controllers.verification import Verification

from datetime import datetime
import logging
import re

class RootHandler(BaseHandler):
	def get(self):
		self.render('landing/index.html',
			title="Wurk Happy &ndash; Online Agreements, Billing, and Payment.")



class SignupHandler(BaseHandler):
	def get(self):
		self.set_status(405)
		self.redirect('/')
	
	def post(self):
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('email', fmt.Email()),
				]
			)
		except fmt.HTTPErrorBetter as e:
			self.set_status(e.status_code)
			self.render('landing/index.html',
				title="Wurk Happy &ndash; Online Agreements, Billing, and Payment.")
		
		if args['email'].count('@') != 1:
			self.set_status(400)
			return
		
		(user, domain) = args['email'].split('@', 1)
		
		r = re.compile(r'^[A-Za-z0-9!#$%&\'*+-\/=?^_`{|}~]+$')
		
		if not r.search(user):
			self.set_status(400)
			return
		
		r = re.compile(r'^([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$')
		
		if not r.search(domain):
			self.set_status(400)
			return
		
		user = User.retrieveByEmail(args['email'])
		
		if not user:
			user = User()
			user['email'] = args['email']
			user['dateCreated'] = datetime.now()
			user.save()
		
		self.render('landing/thankyou.html',
			title="Wurk Happy &ndash; Online Agreements, Billing, and Payment.")
	
class SignupJSONHandler(BaseHandler):
	def get(self):
		self.set_status(405)
		self.redirect('/')
	
	def post(self):
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('email', fmt.Email()),
				]
			)
		except fmt.HTTPErrorBetter:
			self.set_status(400)
			self.renderJSON({
				"success": False,
				"message": (
					"I'm sorry, that didn't look like a proper email address. "
					"Could you please enter a valid email address?"
				)
			})
			return
		
		if args['email'].count('@') != 1:
			self.set_status(400)
			self.renderJSON({
				"success": False,
				"message": (
					"I'm sorry, that didn't look like a proper email address. "
					"Could you please enter a valid email address?"
				)
			})
			return
		
		(user, domain) = args['email'].split('@', 1)
		
		r = re.compile(r'^[A-Za-z0-9!#$%&\'*+-\/=?^_`{|}~]+$')
		
		if not r.search(user):
			self.set_status(400)
			self.renderJSON({
				"success": False,
				"message": (
					"I'm sorry, that didn't look like a proper email address. "
					"Could you please enter a valid email address?"
				)
			})
			return
		
		r = re.compile(r'^([A-Za-z0-9-]+\.)+[A-Za-z]{2,}$')
		
		if not r.search(domain):
			self.set_status(400)
			self.renderJSON({
				"success": False,
				"message": (
					"I'm sorry, that didn't look like a proper email address. "
					"Could you please enter a valid email address?"
				)
			})
			return
		
		logging.info(args['email'])
		user = User.retrieveByEmail(args['email'])
		
		if not user:
			user = User()
			user['email'] = args['email']
			user['dateCreated'] = datetime.now()
			user.save()
		
		self.renderJSON({"success": True})
	

class AboutHandler(BaseHandler):
	def get(self):
		self.render('landing/about.html',
			title="Wurk Happy is in New York City.")



class JobsHandler(BaseHandler):
	def get(self):
		self.render('landing/jobs.html',
			title="Wurk Happy is hiring.")
	
class AboutPersonHandler(BaseHandler):
	def get(self, person):
		self.render('landing/about/%s.html' % person, title='Wurk Happy')

class LegalHandler(BaseHandler):
	def get(self, which):
		self.render('landing/legal/%s.html' % which, title='Wurk Happy &mdash; Legal')

class TechstarsHandler(BaseHandler):
	def get(self):
		self.render('landing/techstars.html', title="About Our Team")

