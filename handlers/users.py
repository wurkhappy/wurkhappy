from __future__ import division
import re

from base import *
from models.user import User, UserPrefs
from models.agreement import *
from models.profile import Profile
import json

from datetime import datetime
import logging

# -------------------------------------------------------------------
# Contact listing
# -------------------------------------------------------------------

class ContactsJSONHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		user = self.current_user
		
		contacts = []
		
		for user in User.iteratorWithContactsForID(user.id):
			contacts.append(user.publicDict())
		
		self.renderJSON({"contacts": contacts})



# -------------------------------------------------------------------
# Profile (Add / Edit)
# -------------------------------------------------------------------

class PreferencesHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self, userID):
		user = self.current_user
		
		prefs = {
			"client_template": "",
			"vendor_template": "",
			"invitation_template": "",
			"agreement_template": "",
			"refund_template": ""
		}
		
		for pref in UserPrefs.iteratorWithUserID(user.id):
			prefs[pref.name] = pref.value
		
		self.render('user/preferences.html', title="My Preferences &ndash; Wurk Happy", bag=prefs, user_id=user.id)
	
class PreferencesJSONHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self, userID):
		user = self.current_user
		
		userDict = user.publicDict()
		userDict['prefs'] = {}
		
		for pref in UserPrefs.iteratorWithUserID(user.id):
			userDict['prefs'][pref.name] = pref.value
		
		self.set_header("Content-Type", "application/json")
		self.renderJSON(userDict)
	
	@web.authenticated
	def post(self, userID):
		user = self.current_user
		
		for arg, value in self.request.arguments.iteritems():
			if arg.startswith('_'):
				continue
			
			userPref = UserPrefs.retrieveByUserIDAndName(user.id, arg)
			
			if not userPref:
				userPref = UserPrefs()
				userPref.userID = user.id
				userPref.name = arg
			
			userPref.value = value[0]
			userPref.save()
		
		self.write(json.dumps({"success": True}))