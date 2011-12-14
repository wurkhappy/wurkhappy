from __future__ import division
import re

from base import *
from controllers import fmt
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
		
		try:
			args = fmt.Parser(self.request.arguments,
				required=[
					('q', fmt.Enforce(str))
				],
				optional=[]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		query = args['q'].lower()
		
		if len(query) < 2:
			contacts = []
		else:
			iterator = User.iteratorWithContactsForID(user.id)
			condition = lambda x: x.getFullName().lower().find(query) > -1 or x.email.lower().find(query) > -1
			
			contacts = [user.publicDict() for user in iterator if condition(user)]
		
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