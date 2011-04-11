import re

from base import *
from models.user import User
from models.profile import Profile
from helpers.verification import Verification
from helpers.validation import Validation

# -------------------------------------------------------------------
# Profile (Add / Edit)
# -------------------------------------------------------------------

class ProfileHandler(Authenticated, BaseHandler):
	ERR = 	{	
			"name_missing":"All name fields are required.",
			"invalid_url":"URLs must be of the format http://website.com."
			}
	def get(self, stub, action):	
		
		# retrieve profile from db based on url stub
		profile = Profile.retrieveByUrlStub(stub)
		
		# if stub doesn't exist, return 404 page
		if not profile:
			self.set_status(404)
			self.write("Not found")
			return
		
		else:
			user = User.retrieveByUserID(profile.userID)
			# if no action was passed, show profile	
			if not action:		
				self.render("user/show_profile.html", title="Profile", user=user, profile=profile, logged_in_user = self.current_user)
				
			# else if action is edit, make sure user is logged in and the logged in user matches the profile, if so render edit page
			elif action == "edit":
				flash = {"error": self.parseErrors()}
				from_reset_password = self.get_argument("rp", None)
				if from_reset_password:
					flash["error"] = ["Your password was reset successfully."]
				logged_in_user = self.current_user
				if not logged_in_user or logged_in_user.id != profile.userID:
					self.set_status(403)
					self.write("Forbidden")
					return
				self.render("user/edit_profile.html", title="Edit Profile", user=user, profile=profile, logged_in_user=self.current_user, flash=flash)
			
	@web.authenticated
	def post(self, *args):
		user = self.current_user
		
		if not user:
			self.set_status(404)
			self.write("Not found")
			return
			
		# Retrieve profile for logged in user
		profile = user.getProfile()

		if not profile:
			# No profile exists yet, so create one and set its userID to the current user
			profile = Profile()
			profile.userID = user.id
		
		# Validations
		# need to make sure user entered a required profile name and other req'd fields!!
		errs = ""
		if not self.get_argument("name", None) or not self.get_argument("firstName", None) or not self.get_argument("lastName", None):
			errs += "name_missing"
		
		blogURL = self.get_argument("blogURL", None)
		portfolioURL = self.get_argument("portfolioURL", None)
		if (blogURL and not Validation.validateURL(blogURL)) or (portfolioURL and not Validation.validateURL(portfolioURL)):
			if errs != "":
				errs += "-"
			errs += "invalid_url"
			
		if errs != "":
			self.redirect('/profile/'+profile.urlStub+"/edit?err="+errs)
		else:		
			# Set user fields
		
			user.firstName = self.get_argument("firstName")
			user.lastName = self.get_argument("lastName")
		
			if self.get_argument('password', None):
				user.password = Verification.hash_password(str(self.get_argument("password")))
		
			# Update profile
			profile.bio = self.get_argument("bio", None)
			profile.name = self.get_argument("name")
			profile.urlStub = re.sub(r'[^\w^d]', r'-', profile.name.lower())
			profile.blogURL = blogURL
			profile.portfolioURL = portfolioURL
			
			user.save()
			profile.save()
		
			self.redirect('/profile/'+profile.urlStub)
			
# -------------------------------------------------------------------
# Profiles (Show / Index)
# -------------------------------------------------------------------

class ProfilesHandler(Authenticated, BaseHandler):
	def get(self, action):
		if action == "new":
			user = self.current_user

			if not user:
				self.set_status(403)
				self.write("Forbidden")
				return
			else:
				# check to see whether user already has a profile
			 	profile = user.getProfile()
				if profile:
					# if so, redirect to the edit profile page
					self.redirect("/profile/"+profile.urlStub+"/edit")
				else:
					# otherwise, create a new profile
					self.render("user/edit_profile.html", title="Create a Profile", user=user, profile=profile, logged_in_user=user, flash={})
		else:
			self.write('index')
