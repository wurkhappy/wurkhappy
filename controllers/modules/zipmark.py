from tornado.web import UIModule
from controllers.orm import ORMJSONEncoder
from controllers.data import Data, Base64, Base58
#from controllers.zipmark import Zipmark
# from controllers.amazonaws import AmazonS3, AmazonFPS

from models.agreement import Agreement, AgreementPhase
from models.user import User
from models.paymentmethod import ZipmarkPaymentMethod

from datetime import datetime
from collections import OrderedDict
import logging
import urllib
import json
from uuid import uuid4



class ConfigureZipmarkAccountButton(UIModule): #, Zipmark_):
	'''Presents an HTML form to initiate the vendor's acceptance of Zipmark's
	terms and conditions. Documentation at the following URL:
	http://...
	'''

	def render(self, vendorID):
		return self.render_string("modules/zipmark/configurebutton.html")



class VerifyZipmarkAccountButton(UIModule):
	'''Display holding pattern HTML.'''

	def render(self, vendorID):
		return self.render_string("modules/zipmark/pleasewait.html")



class PayWithZipmarkButton(UIModule): #, Zipmark):
	'''
	Presents a styled 'action button' link to open the rendered HTML Zipmark
	bill in a new window. No further feedback; should work on that.
	'''
	
	def render(self, phaseID):
		transaction = Transaction.retrieveByAgreementPhaseID(phaseID)
		zipmarkTransaction = ZipmarkTransaction.retrieveByTransactionID(transaction['id'])
		
		namespace = {
			'href': zipmarkTransaction['zipmarkBillURL']
		}
		
		return self.render_string("modules/zipmark/paynowbutton.html", **namespace)

