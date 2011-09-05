from __future__ import division

from base import *
from models.user import User, UserPrefs
from helpers.verification import Verification
from helpers.validation import Validation

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
		details = {
			"userID" : user.id,# just here to make the preference link work
			'actions' : [
				{
					'name' : 'Personal Details',
					'formAction' : '/user/me/account/personal',
					'submit-button' : "Save Personal Details",
					'sections' : [
						{
							'title' : 'Profile Preview',
							'table' : [
								[
									{
										'class' : 'meta',
										'entries' : [
											{
												'value' : '',
												'tags' : [
													('span' ,None),
													('img' , {
														'src' : user.profileSmallURL,
														'width' : '50'
													})
												]
											}
										]
									},{
										'entries' : [
											{
												'value' : " ".join([user.firstName,user.lastName]),
												'tags' : [
													('h3',None),
													('a',{'href' : '/detail.html'})
												]
											},{
												'value' : " ".join([user.email,'-',phoneNumber]),
												'tags' : [('p',None)]
											}
										]
									}
								]
							]
						},{
							'title' : 'Personal Detail',
							'textfields' : [nameLabelValue(name,label,value) for (name,label,value) in [
								("firstName","First Name",user.firstName),
								("lastName","Last Name" ,user.lastName),
								("email" ,"Email",user.email),
								("phoneNumber","Phone Number",phoneNumber)
							]],
							'fileselectors' : {
								"Photo" : [user.profileOrigURL, user.profileSmallURL, user.profileLargeURL]
							}
						}
					]
				},{
					'name' : 'Change Your Password',
					'formAction' : '/user/me/password',
					'submit-button' : "Save New Password",
					'sections' : [
						{
							'title' : 'Change Your Password',
							'textfields' : [nameLabelValue(name,label,value) for (name,label,value) in [
								("old_password","Current Password",""),
								("new_password","New Password" ,""),
								("confirm_new_password","Confirm New Password" ,"")
							]]
						}
					]
				},{
					'name' : 'Credit Card Details',
					'submit-button' : "Save Credit Card Details",
					'formAction' : '/user/me/account/credit',
					'sections' : [
						{
							'title' : 'Stored Credit Card',
							'table' : [
								[
									{
										'entries' : [
											{
												'value' : "**** **** **** 8765",
												'tags' : [('h3',None)]
											},{
												'value' : "Expires: January,2014 - Billing Zip/Postal Code: 01748",
												'tags' : [("p",None)]
											},{
												'value' : "Delete Credit Card",
												'tags' : [
													("p", {"class" : "remove"}),
													("a",{"href" : ""})
												]
											}
										]
									}
								]
							]
						},{
							'title' : 'Credit Card Details',
							'textfields' : [nameLabelValue(name,label,value) for (name,label,value) in [
								("creditCardNumber","Credit Card Number",""),
								("zipCode","Billing Address Zip/Postal Code","")
							]],
							'datefields' : ["Expires On"]
						}
					]
				},{
					'name' : 'Bank Account Details',
					'formAction' : '/user/me/account/bank',
					'submit-button' : "Save Bank Details",
					'sections' : [
						{
							'title' : 'Stored Bank Account',
							'table' : [
								[
									{
										'entries' : [
											{
												'value' : 'Checking Account',
												'tags' : [('h3',None)]
											},{
												'value' : "Routing Number: ******234 - Account Number: *********678",
												'tags' : [('p',None)]
											},{
												'value' : "Delete Bank Account",
												'tags' : [
													('p', {'class' : 'remove'}),
													('a', {'href' : ""})
												]
											}
										]
									}
								]
							]
						},{
							'title' : 'Bank Account Details',
							'radiobuttons' : [nameLabelValue(name,label,value) for (name,label,value) in [
								("checking","pay-checking","Checking Account"),
								("savings","pay-savings","Savings Account")
							]],
							'textfields' : [nameLabelValue(name,label,value) for (name,label,value) in [
								("routingNumber","Routing Number" ,""),
								("accountNumber","Account Number" ,"")
							]]
						}
					]
				}
			]
		}
		
		# userProfile = user.getProfile()
		
		userDict = {
			'id': user.id,
			'firstName': user.firstName,
			'lastName': user.lastName,
			'email': user.email,
			'phoneNumber': '', # userProfile.phoneNumber,
			'profileURL': [
				user.profileSmallURL,
				user.profileLargeURL
			]
		}
		
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
	    args = self.request.arguments
	    userData = User.retrieveByUserID(self.current_user.id)
	    if not userData:
		    userData = User()
	    userData.firstName = args['firstName'][0]
	    userData.lastName = args['lastName'][0]
	    if Validation.validateEmail(args['email'][0]):
		    userData.email = args['email'][0]
	    else:
		    raise RuntimeError('Do something javascripty here')
	    if 'phoneNumber' in dir(userData):
		    userData.phoneNumber = args['phoneNumber'][0]
	    userData.save()
	    self.write(json.dumps({"success": True}))



# -------------------------------------------------------------------
# PasswordJSONHandler
# -------------------------------------------------------------------

class PasswordJSONHandler(Authenticated, BaseHandler):

	@web.authenticated
	def post(self):
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('old_password', fmt.Enforce(str)),
					('new_password', fmt.Enforce(str)),
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		if not (user and user.passwordIsValid(args['old_password'])):
			# User wasn't found, or password is wrong, display error
			#TODO: Exponential back-off when user enters incorrect password.
			#TODO: Flag accounds if passwords change too often.
			error = {
				"domain": "web.request",
				"debug": "please validate authentication credentials"
			}
			self.set_status(401)
			self.write(json.dumps(error))
		else:
			user.setPasswordHash(args['new_password'])# = Verification.hash_password(str(args['new_password']))
			user.save()
			self.write(json.dumps({"success": True}))
		
		print self.get_argument('old_password'), self.get_argument('new_password')
		user = self.current_user



# -------------------------------------------------------------------
# BankJSONHandler
# -------------------------------------------------------------------

class BankJSONHandler(Authenticated, BaseHandler):

	@web.authenticated
	def post(self):
		print 'BankJSONHandler'

# -------------------------------------------------------------------
# CreditJSONHandler
# -------------------------------------------------------------------

class CreditJSONHandler(Authenticated, BaseHandler):

	@web.authenticated
	def post(self):
		print 'CreditJSONHandler'
