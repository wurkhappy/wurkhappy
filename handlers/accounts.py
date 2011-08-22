from __future__ import division

from base import *
from models.user import User, UserPrefs

try:
	import json
except:
	import simplejson as json

from datetime import datetime
import logging


# -------------------------------------------------------------------
# AccountHandler
# -------------------------------------------------------------------

class AccountHandler(Authenticated, BaseHandler):

    @web.authenticated
    def get(self):
        # inherited from web.RequestHandler:
        user = self.current_user

        details = {"userID" : user.id # just here to make the preference link work
		   , 'actions' : [{'name' : 'Personal Details'
				   , 'title' : 'Profile Preview'
				   , 'textfields' : {"First Name" : user.firstName
						   ,"Last Name" : user.lastName
						   , "Email" : user.email
						   , "Phone Number" : ("phoneNumber" in dir(user) and user.phoneNumber) or ""
						   }
				   ,'fileselectors' : {"Photo" : [user.profileOrigURL, user.profileSmallURL, user.profileLargeURL]}
				   , 'method' : 'GET'
				   ,'params' : ""}
				  ,{'name' : 'Change Your Password' 
				    , 'title' : 'Change Your Password'
				    , 'textfields' : {}
				    , 'fileselectors' : {}
				    ,'action' : "/usr/me/tab.json"
				    , 'method' : 'GET'
				    ,'params' : ""}
				  , {'name' : 'Credit Card Details'
				     , 'title' : 'Stored Credit Card'
				    , 'textfields' : {}
				    , 'fileselectors' : {}
				     ,'action' : "/usr/me/tab.json"
				     , 'method' : 'GET'
				     ,'params' : ""}
				  , {'name' : 'Bank Account Details'
				     , 'title' : 'Stored Bank Account'
				    , 'textfields' : {}
				    , 'fileselectors' : {}
				     , 'action' : "/usr/me/tab.json"
				     , 'method' : 'GET'
				     , 'params' : ""}]
		   }
		   
	html = 'new_from_designer/admin/account.html'
	torn_html = 'user/account.html'
        self.render(torn_html, title="Hello, World!", bag=details, user_id=user.id, current="")


# -------------------------------------------------------------------
# AccountJSONHandler
# -------------------------------------------------------------------

class AccountJSONHandler(Authenticated, BaseHandler):
    @web.authenticated
    def get(self, userID):
        user = self.current_user

        userDict = user.publicDict()
        userDict['details'] = {"firstName" : user.firstName
                               ,"lastName" : user.lastName
                               , "profileURL" : [user.profileOrigURL, user.profileSmallURL, user.profileLargeURL]
                               , "email" : user.email
                               , "phoneNumber" : user.phoneNumber or ""
                               }

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

