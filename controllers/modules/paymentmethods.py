from tornado.web import UIModule
from controllers.orm import ORMJSONEncoder
from controllers.data import Data, Base64, Base58

from models.user import User
from models.paymentmethod import (
	PaymentBase, OOBPaymentMethod, AmazonPaymentMethod, ZipmarkPaymentMethod
)

from collections import OrderedDict
import logging
import json



class AcceptMarketplaceFeeButton(UIModule, AmazonFPS):
	'''Presents an HTML form to initiate the vendor's acceptance of Amazon's
	marketplace fees and terms and conditions. Documentation at the following URL:
	http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/marketplace-fee-input.html
	'''
	
	def render(self, vendorID):
		pass

class PaymentMethodSetup(UIModule):
	'''Presents an HTML interface to configure new payment methods or to edit
	account settings for existing payment methods.
	'''

	def render(self, user):
		# Get all payment method subclasses
		paymentMethods = []
		didFindPaymentMethod = False

		for c in PaymentBase.__subclasses__():
			pm = c.retrieveByUserID(user['id'])

			if pm:
				didFindPaymentMethod = True

			paymentMethods.append(pm or c())
		
		return self.render_string(
			'modules/paymentmethod/settings.html',
			paymentMethods=paymentMethods,
			didFindPaymentMethod=didFindPaymentMethod
		)

