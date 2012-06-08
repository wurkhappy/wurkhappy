from tornado.web import UIModule
from controllers.orm import ORMJSONEncoder
from controllers.data import Data, Base64, Base58
from controllers.amazonaws import AmazonFPS

from models.agreement import Agreement, AgreementPhase
from models.user import User, UserPrefs

from datetime import datetime
from collections import OrderedDict
import logging
import urllib
import json
from uuid import uuid4



class AcceptMarketplaceFeeButton(UIModule, AmazonFPS):
	'''Presents an HTML form to initiate the vendor's acceptance of Amazon's
	marketplace fees and terms and conditions. Documentation at the following URL:
	http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/marketplace-fee-input.html
	'''
	
	def render(self, vendorID):
		accessKey = self.handler.application.configuration['amazonaws']['key_id']
		secretKey = self.handler.application.configuration['amazonaws']['key_secret']
		httpVerb = 'GET'
		fpsHost = self.handler.application.configuration['amazonaws']['simple_pay_host']
		fpsURI = self.handler.application.configuration['amazonaws']['fps_accept_fee_uri']
		
		vendor = User.retrieveByID(vendorID)
		
		data = OrderedDict()
		
		data['callerKey'] = accessKey
		data['callerReference'] = Data(uuid4().get_bytes()).stringWithEncoding(Base58)
		data['collectEmailAddress'] = "true"
		data['maxVariableFee'] = "3.00"
		data['pipelineName'] = "Recipient"
		data['recipientPaysFee'] = "false"
		data['returnURL'] = '{0}://{1}/user/me/account'.format(
			self.request.protocol, self.handler.application.configuration['wurkhappy']['hostname']
		)
		data['signatureMethod'] = "HmacSHA256"
		data['signatureVersion'] = "2"
		
		data['signature'] = self.generateSignature(httpVerb, fpsHost, fpsURI, data, secretKey)
		
		return self.render_string(
			"modules/amazon/simplepaybutton.html",
			method=httpVerb,
			action='https://{0}/{1}'.format(fpsHost, fpsURI),
			buttonImageURL='https://payments.amazon.com/img/marketplace_fee_with_logo_orange.gif',
			data=data
		)



class PayWithAmazonButton(UIModule, AmazonFPS):
	'''Presents an HTML form to initiate a payment via the Amazon Simple Pay Marketplace. Documentation here:
	http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/marketplace-pay-input.html
	'''
	
	def render(self, phaseID):
		accessKey = self.handler.application.configuration['amazonaws']['key_id']
		secretKey = self.handler.application.configuration['amazonaws']['key_secret']
		httpVerb = 'POST'
		fpsHost = self.handler.application.configuration['amazonaws']['simple_pay_host']
		fpsURI = self.handler.application.configuration['amazonaws']['fps_make_payment_uri']
		
		phase = AgreementPhase.retrieveByID(phaseID)
		agreement = Agreement.retrieveByID(phase['agreementID'])
		vendor = User.retrieveByID(agreement['vendorID'])
		email = UserPrefs.retrieveByUserIDAndName(vendor['id'], 'amazon_recipient_email')
		token = UserPrefs.retrieveByUserIDAndName(vendor['id'], 'amazon_token_id')
		
		data = OrderedDict()
	
		data['abandonURL'] = '{0}://{1}/agreement/{2}'.format(
			self.request.protocol,
			self.handler.application.configuration['wurkhappy']['hostname'],
			agreement['id']
		) # TODO: Fixme!
		data['accessKey'] = accessKey
		data['amount'] = phase.getCostString('USD ', 'USD 0.00')
		data['description'] = phase['description']
		data['immediateReturn'] = 'true'
		data['ipnUrl'] = '{0}://{1}/callbacks/amazon/simplepay/paymentnotification'.format(
			self.request.protocol, self.handler.application.configuration['wurkhappy']['hostname']
		)
		data['processImmediate'] = 'true'
		data['recipientEmail'] = email['value']
		data['referenceId'] = Data(uuid4().get_bytes()).stringWithEncoding(Base58)
		data['returnUrl'] = '{0}://{1}/agreement/{2}'.format(
			self.request.protocol,
			self.handler.application.configuration['wurkhappy']['hostname'],
			agreement['id']
		)
		data['signatureMethod'] = "HmacSHA256"
		data['signatureVersion'] = "2"
		data['variableMarketplaceFee'] = "3.00"
		
		data['signature'] = self.generateSignature(httpVerb, fpsHost, fpsURI, data, secretKey)
		
		return self.render_string(
			"modules/amazon/simplepaybutton.html",
			method=httpVerb,
			action='https://{0}/{1}'.format(fpsHost, fpsURI),
			buttonImageURL='https://images-na.ssl-images-amazon.com/images/G/01/asp/golden_large_paynow_withlogo_darkbg.gif',
			data=data
		)


