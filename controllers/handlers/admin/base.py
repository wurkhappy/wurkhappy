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
		# Nasty hack below, but get_secure_cookie returns None on failure, which breaks the MySQL query
		user = User.retrieveByID(self.get_secure_cookie("user_id") or 0)
		if user:
			admin = UserPrefs.retrieveByUserIDAndName(user['id'], 'isSuperuser')
			return admin and user
		else:
			return None
