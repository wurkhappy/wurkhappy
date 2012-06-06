from base import BaseHandler



# -------------------------------------------------------------------
# Terms and Conditions
# -------------------------------------------------------------------
# This is mostly static and should probably be handled by a rewrite
# rule in Nginx to an HTML document in the static directory.

class TermsHandler(BaseHandler):
	def get(self):
		self.render('legal/terms.html', title='Terms of Use &ndash; Wurk Happy')



# -------------------------------------------------------------------
# Privacy Policy
# -------------------------------------------------------------------
# This is mostly static and should probably be handled by a rewrite
# rule in Nginx to an HTML document in the static directory.

class PrivacyHandler(BaseHandler):
	def get(self):
		self.render('legal/privacy.html', title='Privacy Policy &ndash; Wurk Happy')
