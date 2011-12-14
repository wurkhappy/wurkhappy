import tornado.web as web
from models.user import User

from controllers.orm import ORMJSONEncoder
import json



class BaseHandler(web.RequestHandler):
	def set_secure_cookie(self, name, value, expires_days=30, **kwargs):
		kwargs['httponly'] = True
		
		if self.request.protocol == 'https':
			kwargs['secure'] = True
		
		web.RequestHandler.set_secure_cookie(
			self, name, value, expires_days, **kwargs
		)
	
	def authenticated(self, method):
		pass
	
	def superuser(self, method):
		pass
	
	# What is this for? I think Jamie wrote it, but I don't think it's used anywhere...
	def parseErrors(self):
		err = self.get_argument("err", None)
		if err:
			err = err.split('-')
			return [self.ERR.get(e) for e in err]
		else:
			return None
	
	def renderJSON(self, obj):
		self.set_header('Content-Type', 'application/json')
		self.write(json.dumps(obj, cls=ORMJSONEncoder))



class Authenticated(object):
	def get_current_user(self):
		userID = self.get_secure_cookie("user_id")
		return userID and User.retrieveByID(userID)

	def _is_superuser(self):
		pass