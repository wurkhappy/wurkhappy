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
		data = {'_xsrf': self.xsrf_token}
		self.render("auth/login.html", title="Sign In", error=None, data=data)



class LoginJSONHandler(BaseHandler):
	def post(self):
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('email', fmt.Email()),
					('user_id', fmt.PositiveInteger())
				],
				required=[
					('password', fmt.Enforce(str))
				]
			)
		except fmt.HTTPErrorBetter as e:
			error = {
				"domain": "authentication",
				"display": (
					"I'm sorry, that didn't look like a proper email "
					"address. Could you please enter a valid email address?"
				),
				"debug": "'email' parameter must be well-formed"
			}

			self.set_status(400)
			self.renderJSON(error)

		user = User.retrieveByEmail(args['email'])

		if not user or not user.passwordIsValid(args['password']):
			# User wasn't found or password is wrong.
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
			self.renderJSON(error)
			return

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
			self.renderJSON(error)
		else:
			self.set_secure_cookie("user_id", str(user['id']))
			self.renderJSON(user.getPublicDict())



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
