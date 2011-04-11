import tornado.web as web
from model.user import User

class BaseHandler(web.RequestHandler):
	def authenticated(self, method):
		pass
	
	def superuser(self, method):
		pass
		
	def parseErrors(self):
		err = self.get_argument("err", None)
		if err:
			err = err.split('-')
			return [self.ERR.get(e) for e in err]
		else:
			return None
			
class Authenticated(object):
	def get_current_user(self):
		userID = self.get_secure_cookie("user_id")
		return userID and User.retrieveByID(userID)

	def _is_superuser(self):
		pass