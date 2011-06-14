from base import *

class RootHandler(BaseHandler):
	def get(self):
		self.write("How are you gentlemen!")

class SignupHandler(BaseHandler):
	def get(self):
		pass
	def post(self):
		pass
	
class AboutHandler(BaseHandler):
	def get(self):
		pass
	
class JobsHandler(BaseHandler):
	def get(self):
		pass
	
