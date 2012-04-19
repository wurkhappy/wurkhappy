from base import *


class RootHandler(Authenticated, BaseHandler):
	
	# Even though the get method does not require authentication, we need to
	# inherit from `Authenticated` in order to have access to the overridden
	# `get_current_user` method.
	
	def get(self):
		if self.get_current_user():
			self.redirect('/agreements/with/clients')
		else:
			self.redirect('/login')
