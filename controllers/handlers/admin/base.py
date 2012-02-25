import tornado.web as web
from models.user import User, UserPrefs

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
	
	def renderJSON(self, obj):
		self.set_header('Content-Type', 'application/json')
		self.write(json.dumps(obj, cls=ORMJSONEncoder))



class Authenticated(object):
	def get_current_user(self):
		user = User.retrieveByID(self.get_secure_cookie("user_id"))
		if user:
			admin = UserPrefs.retrieveByUserIDAndName(user['id'], 'isSuperuser')
			return admin and user
		else:
			return None
