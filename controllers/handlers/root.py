from base import *

class RootHandler(BaseHandler):
	def get(self):
		if self.current_user:
			self.redirect('/agreements/with/clients')
		else:
			self.redirect('/login')
