from base import BaseHandler, Authenticated

class RootHandler(Authenticated, BaseHandler):
	def get(self):
		if self.current_user:
			self.redirect('/users')
		else:
			self.redirect('/login')
