from __future__ import division
import re

from base import *
from models.user import User, UserPrefs
from models.agreement import *
from models.profile import Profile

try:
	import json
except:
	import simplejson as json

from datetime import datetime
import logging

# -------------------------------------------------------------------
# Profile (Add / Edit)
# -------------------------------------------------------------------

class PreferencesHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self, userID):
		pass
	
class PreferencesJSONHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self, userID):
		user = self.current_user
		
		userDict = user.publicDict()
		userDict['prefs'] = {}
		
		for pref in UserPrefs.iteratorWithUserID(user.id):
			userDict['prefs'][pref.name] = pref.value
		
		self.set_header("Content-Type", "application/json")
		self.write(json.dumps(userDict))
	
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