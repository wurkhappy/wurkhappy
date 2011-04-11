from base import *

class RootHandler(BaseHandler):
	def get(self):
		self.write("How are you gentlemen!")
