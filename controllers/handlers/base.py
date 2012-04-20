import tornado.web as web
from models.user import User

from controllers.orm import ORMJSONEncoder
from hashlib import sha1
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
	
	def renderJSON(self, obj):
		self.set_header('Content-Type', 'application/json')
		self.write(json.dumps(obj, cls=ORMJSONEncoder))
	
	def write_error(self, statusCode, **kwargs):
		self.render('error/404.html', title="Uh-oh &ndash; Wurk Happy", data=dict())



# -------------------------------------------------------------------
# RequestHandler subclass that can serialize JSON objects
# -------------------------------------------------------------------

class JSONBaseHandler(web.RequestHandler):
	
	def renderJSON(self, obj):
		self.set_header('Content-Type', 'application/json')
		self.write(json.dumps(obj, cls=ORMJSONEncoder))



# -------------------------------------------------------------------
# Cookie authentication mix-in
# -------------------------------------------------------------------

class Authenticated(object):
	'''Authentication mix-in for Wurk Happy. Identifies users by querying for
	a secure cookie and looking up the resulting ID in the database.'''
	
	def get_current_user(self):
		# TODO: I think this is handled by TokenAuthenticated.
		# Make sure it's not used anywhere before deleting!
		self.token = self.get_argument("t", None)
		
		userID = self.get_secure_cookie("user_id")
		return userID and User.retrieveByID(userID)
	
	def superuser(self, method, *args, **kwargs):
		def wrapped(method):
			return method(*args, **kwargs)
		return wrapped



# -------------------------------------------------------------------
# Token (and cookie) authentication mix-in
# -------------------------------------------------------------------

class TokenAuthenticated(object):
	'''Alternative authentication mix-in for classes that accept users
	identified by log-in tokens. The token is usually specified as a query-
	string argument called `t`.'''
	
	def get_current_user(self):
		userID = self.get_secure_cookie("user_id")
		user = userID and User.retrieveByID(userID)
		self.token = None
		
		if not user:
			self.token = self.get_argument("t", None)
			user = self.token and User.retrieveByFingerprint(sha1(self.token).hexdigest())
		
		return user