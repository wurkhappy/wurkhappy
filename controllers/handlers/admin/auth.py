from tornado import web
from base import BaseHandler, Authenticated
from controllers import fmt
from models.user import User, UserPrefs
import logging

# -------------------------------------------------------------------
# Login
# -------------------------------------------------------------------

class LoginHandler(BaseHandler):
	def get(self):
		self.render("auth/login.html", title="Sign In", error=None)
	
	
	def post(self):
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('email', fmt.Email()),
					('password', fmt.Enforce(str))
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			logging.warn(e.message)
			
			error = {
				"domain": "authentication",
				"display": (
					"I'm sorry, that didn't look like a proper email "
					"address. Could you please enter a valid email address?"
				),
				"debug": "'email' parameter must be well-formed"
			}
			
			self.set_status(400)
			self.render("user/login.html", title="Sign In to Wurk Happy", error=error)
			return
		
		user = User.retrieveByEmail(args['email'])
		
		if not user or not user.passwordIsValid(args['password']):
			# User wasn't found, or password is wrong, render login with error
			error = {
				"domain": "authentication",
				"display": (
					"I'm sorry, the email and password combination you "
					"entered doesn't match any of our records. Please check "
					"for typos and make sure caps lock is turned off when "
					"entering your password."
				),
				"debug": "incorrect email or password"
			}
			
			self.set_status(401)
			self.render("auth/login.html", title="Sign In to Wurk Happy", error=error)
		
		superuser = UserPrefs.retrieveByUserIDAndName(user['id'], 'isSuperuser')
		
		if not superuser:
			error = {
				"domain": "authentication",
				"display": (
					"I'm sorry, the username and password combination is incorrect."
				),
				"debug": "incorrect credentials"
			}
			self.set_status(401)
			self.render("auth/login.html", title="Sign In to Wurk Happy", error=error)
		else:
			self.set_secure_cookie("user_id", str(user['id']))
			self.redirect('/users')



# -------------------------------------------------------------------
# Logout 
# -------------------------------------------------------------------

class LogoutHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		self.clear_cookie("user_id")
		self.redirect('/login')

	@web.authenticated
	def post(self):
		self.set_status(404)
		self.write("Not found")
