from base import *
from models.user import *
from helpers.verification import Verification

import logging

class RootHandler(BaseHandler):
	def get(self):
		self.render('landing/index.html',
			title="Wurk Happy - Our work agreements get you paid faster.")



class SignupHandler(BaseHandler):
	def get(self):
		self.redirect('/')
	
	def post(self):
		email = self.get_argument("email", None)
		logging.info(email)
		# user = User()
		# user.email = email
		# user.confirmed = 0
		# # user.invited = 0
		# user.dateCreated = datetime.now()
		# verifier = Verification()
		# user.confirmationCode = verifier.code
		# user.confirmationHash = verifier.hashDigest
		# user.save()
		
		self.render('landing/thankyou.html',
			title="Wurk Happy - Our work agreements get you paid faster.")
	
class AboutHandler(BaseHandler):
	def get(self):
		self.render('landing/about.html')



class JobsHandler(BaseHandler):
	def get(self):
		self.render('landing/jobs.html')

