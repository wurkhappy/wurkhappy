from base import BaseHandler



# -------------------------------------------------------------------
# Frequently Asked Questions
# -------------------------------------------------------------------
# This is mostly static and should probably be handled by a rewrite
# rule in Nginx to an HTML document in the static directory.

class FAQHandler(BaseHandler):
	def get(self):
		self.render('help/faq.html', title='Frequently Asked Questions &ndash; Wurk Happy')
