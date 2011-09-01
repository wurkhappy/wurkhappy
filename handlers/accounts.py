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

	def nameLabelValue(name, label, value):
		return {"name" : name, "label" : label, "value" : value}

	phoneNumber = ("phoneNumber" in dir(user) and user.phoneNumber) or ""
        details = {"userID" : user.id # just here to make the preference link work
		   , 'actions' : [{'name' : 'Personal Details'
				   , 'submit-button' : "Save Personal Details"
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
						     , 'textfields' : [nameLabelValue(name,label,value) for (name,label,value) in \
									       [("firstName", "First Name", user.firstName)
										,("lastName", "Last Name" , user.lastName)
										,("email" , "Email", user.email)
										,("phoneNumber", "Phone Number", phoneNumber)]]
						     , 'fileselectors' : {"Photo" : [user.profileOrigURL, user.profileSmallURL, user.profileLargeURL]}
						     }]
				   }
				  ,{'name' : 'Change Your Password' 
				    , 'submit-button' : "Save New Password"
				    , 'sections' : [{'title' : 'Change Your Password'
						     , 'textfields' : [nameLabelValue(name,label,value) for (name,label,value) in \
									       [("old_password", "Current Password", "")
										,("new_password","New Password" , "")
										,("new_password", "Confirm New Password" , "")]]
						     }]}
				  , {'name' : 'Credit Card Details'
				     , 'submit-button' : "Save Credit Card Details"
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
							, 'textfields' : [nameLabelValue(name,label,value) for (name,label,value) in \
										  [("creditCardNumber","Credit Card Number","")
										   ,("zipCode","Billing Address Zip/Postal Code", "")]]
							, 'datefields' : ["Expires On"]}
						     ]}
				  ,{'name' : 'Bank Account Details'
				    , 'submit-button' : "Save Bank Details"
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
						     , 'radiobuttons' : [nameLabelValue(name,label,value) for (name,label,value) in \
										 [("checking","pay-checking", "Checking Account")
										  , ("savings","pay-savings", "Savings Account")]]
						       , 'textfields' : [nameLabelValue(name,label,value) for (name, label,value) in \
										 [("routingNumber", "Routing Number" , "")
										  ,("accountNumber", "Account Number" , "")]]
						       }]}]}
		   
	html = 'new_from_designer/admin/account.html'
	torn_html = 'user/account.html'
        self.render(torn_html, title="My Account: Personal Details", bag=details, user_id=user.id, current="")

    @web.authenticated
    def post(self):
	    print 'AccountHandler post'


# -------------------------------------------------------------------
# AccountJSONHandler
# -------------------------------------------------------------------

class AccountJSONHandler(Authenticated, BaseHandler):

    @web.authenticated
    def post(self):
	    print 'AccountJSONHandler post'
	    user = self.current_user
	    for arg, value in self.request.arguments.iteritems():
		    if arg.startswith('_'):
			    continue
		
		    print arg, value
		    userData = User.retrieveByUserID(user.id)
		    
		    if not userData:
			    # note : may need to use a keyword to set here in 2.7+
			    userData = User()
		    
		    if arg in dir(userData):
			    setattr(userData, arg, value[0])
			    userData.save()
		
	    self.write(json.dumps({"success": True}))
