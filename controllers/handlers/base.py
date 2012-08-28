import tornado.web as web
from models.user import User

from controllers.orm import ORMJSONEncoder
from hashlib import sha1
import logging
import json
import sys
import functools
from datetime import datetime


class BaseHandler(web.RequestHandler):
	def set_secure_cookie(self, name, value, expires_days=30, **kwargs):
		kwargs['httponly'] = True
		
		if self.request.protocol == 'https':
			kwargs['secure'] = True
		
		web.RequestHandler.set_secure_cookie(
			self, name, value, expires_days, **kwargs
		)
	
	def authenticated(self, method):
		raise NotImplementedError('Incorrect import order. ' +
			'The authentication mixin should be first.')
	
	def renderJSON(self, obj):
		self.set_header('Content-Type', 'application/json')
		self.finish(json.dumps(obj, cls=ORMJSONEncoder))
	
	def write_error(self, statusCode, **kwargs):
		self.render('error/404.html', title="Uh-oh &ndash; Wurk Happy", data=dict())



# -------------------------------------------------------------------
# RequestHandler subclass that can serialize JSON objects
# -------------------------------------------------------------------

class JSONBaseHandler(web.RequestHandler):
	
	@staticmethod
	def authenticated(method):
		"""Decorate methods with this to require that the user be logged in."""
		@functools.wraps(method)
		def wrapper(self, *args, **kwargs):
			if not self.current_user:
				if self.request.method in ("GET", "HEAD"):
					url = self.get_login_url()
					if "?" not in url:
						if urlparse.urlsplit(url).scheme:
							# if login url is absolute, make next absolute too
							next_url = self.request.full_url()
						else:
							next_url = self.request.uri
						url += "?" + urllib.urlencode(dict(next=next_url))
					self.redirect(url)
					return
				self.error_description = {
					'domain': 'authentication',
					'display': 'It is forbidden!',
					'debug': 'the requested action is forbidden'
				}
				raise web.HTTPError(403)
			return method(self, *args, **kwargs)
		return wrapper
	
	def renderJSON(self, obj):
		self.set_header('Content-Type', 'application/json')
		self.finish(json.dumps(obj, cls=ORMJSONEncoder))

	def write_error(self, status_code, **kwargs):
		if hasattr(self, 'error_description'):
			self.renderJSON(self.error_description)
		else:
			super(JSONBaseHandler, self).write_error(status_code, **kwargs)

	def _handle_request_exception(self, e):
		if isinstance(e, web.HTTPError):
			super(JSONBaseHandler, self)._handle_request_exception(e)
		else:
			logging.error("Uncaught exception %s", self._request_summary(),
				exc_info=True)
			self.send_error(500, exc_info=sys.exc_info())
			# TODO: Send pretty JSON error instead of default 500



# -------------------------------------------------------------------
# General authentication mix-in
# -------------------------------------------------------------------

class Authenticated(object):
	'''Authentication mix-in for Wurk Happy. Identifies users by
	querying for a secure cookie and looking up the resulting ID in
	the database.'''
	
	def setAuthCookiesForUser(self, user, mode='cookie'):
		'''Set appropriate authentication cookies for the specified
		user.'''
		
		self.set_secure_cookie('user_id', str(user['id']), httponly=True)
		self.set_secure_cookie('auth', mode, httponly=True)
		if mode == 'cookie':
			# TODO: this is a hacky way to remove microsecond precision in the timestamp. Not that we use it at the moment.
			self.set_secure_cookie('auth_timestamp', datetime.utcnow().isoformat().split('.')[0] + 'Z', expires_days=1)
	
	def get_current_user(self):
		'''Return the currently authenticated user, identified by
		cookie. Sets authMethod property of the user object. Allows
		users whose cookies were set by a previous authentication
		via email token.'''
		
		userID = self.get_secure_cookie('user_id')
		user = userID and User.retrieveByID(userID)
		if user:
			user.authMethod = self.get_secure_cookie('auth')
		return user



# -------------------------------------------------------------------
# Cookie authentication mix-in
# -------------------------------------------------------------------

class CookieAuthenticated(Authenticated):
	'''Authentication mix-in for Wurk Happy. Identifies users by
	querying for a secure cookie and looking up the resulting ID in
	the database.'''

	def get_current_user(self):
		'''Return the currently authenticated user, identified by
		cookie. Sets authMethod property of the user object. Returns
		None if user is authenticated via email token.'''

		userID = self.get_secure_cookie('user_id')
		user = userID and User.retrieveByID(userID)
		authMethod = self.get_secure_cookie('auth')
		
		if authMethod == 'token':
			return None
		
		if user:
			user.authMethod = authMethod
		
		return user



# -------------------------------------------------------------------
# Token (and cookie) authentication mix-in
# -------------------------------------------------------------------

class TokenAuthenticated(Authenticated):
	'''Alternative authentication mix-in for classes that accept users
	identified by log-in tokens. The token is specified as a query-
	string argument called `t`.'''
	
	def get_current_user(self):
		'''Return the currently authenticated user, either identified
		by token argument or by user ID cookie. Sets appropriate
		cookies as a side effect.'''
		
		# Authentication Flowchart                                   
		# 
		#        ( A )                     A. read token & cookie    
		#          |                                                 
		#        < B > --- no ---+         B. is token set?          
		#          |             |                                   
		#         yes          ( C )       C. retrieve user by ID    
		#          |                                                 
		#        < D > --- no ---+         D. is token valid?        
		#          |             |                                   
		#         yes          ( E )       E. delete cookies; error  
		#          |                                                 
		#        < F > --- no ---+         F. does token match?      
		#          |             |                                   
		#         yes          ( G )       G. issue new cookies      
		#          |                                                 
		#        ( H )                     H. use existing cookies   
		# 
		
		self.token = self.get_argument('t', None)
		userID = self.get_secure_cookie('user_id')
		authMethod = self.get_secure_cookie('auth', 'token')
		
		if self.token:
			user = User.retrieveByToken(self.token)
			
			if user:
				if user['id'] != userID:
					self.setAuthCookiesForUser(user, mode='token')
					user.authMethod = 'token'
				else:
					user.authMethod = authMethod
			else:
				self.clear_cookie('user_id')
				self.clear_cookie('auth')
				user = None
		elif userID:
			user = User.retrieveByID(userID)
			user.authMethod = authMethod
		else:
			user = None
		
		return user
