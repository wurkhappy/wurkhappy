from controllers.handlers.base import Authenticated, JSONBaseHandler
from tornado.web import HTTPError
from collections import OrderedDict



# -------------------------------------------------------------------
# HTTP Server Test Handler
# -------------------------------------------------------------------

class HTTPServerTestHandler(Authenticated, JSONBaseHandler):
	
	def get(self):
		if self.current_user is None:
			raise HTTPError(403)
		
		response = OrderedDict([
			('user', self.current_user['id']),
			('remote_ip', self.request.remote_ip),
			('protocol', self.request.protocol),
			('arguments', self.request.arguments)
		])
		
		self.renderJSON(response)