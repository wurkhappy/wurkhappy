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
	phoneNumber = ("phoneNumber" in dir(user) and user.phoneNumber) or ""
        details = {"userID" : user.id # just here to make the preference link work
		   , 'actions' : [{'name' : 'Personal Details'
				   , 'sections' : [{'title' : 'Profile Preview'
						    , 'table' : [[{'class' : 'meta'
								   , 'entries' : [{'value' : ''
										   , 'tags' : [('span' , None)
											       ,('img' , {'src' : user.profileSmallURL
													  ,'width' : '50'})]}]}
								  ,{'entries' : [{'value' : " ".join([user.firstName, user.lastName])
										  ,'tags' : [('h3', None)
											     ,('a', {'href' : '/detail.html'})]}
										 ,{'value' : " ".join([user.email, '-', phoneNumber])
										   ,'tags' : [('p', None)]}]}
								  ]]}
						   ,{'title' : 'Personal Detail'
						     , 'textfields' : {"First Name" : user.firstName
								       ,"Last Name" : user.lastName
								       , "Email" : user.email
								       , "Phone Number" : phoneNumber
								       }
						     , 'fileselectors' : {"Photo" : [user.profileOrigURL, user.profileSmallURL, user.profileLargeURL]}
						     }]
				   }
				  ,{'name' : 'Change Your Password' 
				    , 'sections' : [{'title' : 'Change Your Password'
						     , 'textfields' : {"Current Password" : ""
								       ,"New Password" : ""
								       , "Confirm New Password" : ""}
						     }]}
				  , {'name' : 'Credit Card Details'
				     , 'sections' : [{'title' : 'Stored Credit Card'
						      , 'table' : [[{'entries' : [{'value' : "**** **** **** 8765"
										   ,'tags' : [('h3', None)]}
										  ,{'value' : "Expires: January, 2014 - Billing Zip/Postal Code: 01748"
										    , 'tags' : [("p", None)]}
										  ,{'value' : "Delete Credit Card"
										    ,'tags' : [("p", {"class" : "remove"})
											       ,("a", {"href" : ""})]}]}
								    ]]}
						     , {'title' : 'Credit Card Details'
							, 'textfields' : {"Credit Card Number" : ""
									  ,"Billing Address Zip/Postal Code" : ""}
							, 'datefields' : ["Expires On"]}
						     ]}
				  ,{'name' : 'Bank Account Details'
				    , 'sections' : [{'title' : 'Stored Bank Account'
						     ,'table' : [[{'entries' : [{'value' : 'Checking Account'
										 , 'tags' : [('h3', None)]}
										,{'value' : "Routing Number: ******234 - Account Number: *********678"
										  , 'tags' : [('p', None)]}
										,{'value' : "Delete Bank Account"
										  , 'tags' : [('p', {'class' : 'remove'})
											      ,('a', {'href' : ""})]}]}
								  ]]}
						    , {'title' : 'Bank Account Details'
						     , 'radiobuttons' : [{"value" : "Checking Account"
									  ,"label" : "pay-checking"
									  ,"name" : "checking"}
									 ,{"value" : "Savings Account"
									   ,"label" : "pay-savings"
									   ,"name" : "savings"}]
						       , 'textfields' : {"Routing Number" : ""
									 ,"Account Number" : ""}}]}]}
		   
	html = 'new_from_designer/admin/account.html'
	torn_html = 'user/account.html'
        self.render(torn_html, title="My Account: Personal Details", bag=details, user_id=user.id, current="")


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

