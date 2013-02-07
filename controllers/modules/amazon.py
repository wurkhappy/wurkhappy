from tornado.web import UIModule
from controllers.orm import ORMJSONEncoder
from controllers.data import Data, Base64, Base58
from controllers.amazonaws import AmazonS3, AmazonFPS

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
		accessKey = AmazonS3.getSettingWithTag('key_id')
		secretKey = AmazonS3.getSettingWithTag('key_secret')
		httpVerb = 'GET'
		fpsHost = AmazonS3.getSettingWithTag('simple_pay_host')
		fpsURI = AmazonS3.getSettingWithTag('fps_accept_fee_uri')
		
		vendor = User.retrieveByID(vendorID)
		
		data = OrderedDict()
		
		data['callerKey'] = accessKey
		data['callerReference'] = Data(uuid4().get_bytes()).stringWithEncoding(Base58)
		data['collectEmailAddress'] = "true"
		data['maxVariableFee'] = "2.9"
		data['pipelineName'] = "Recipient"
		data['recipientPaysFee'] = "true"
		data['returnURL'] = '{0}://{1}/user/me/account'.format(
			self.request.protocol, self.handler.application.configuration['wurkhappy']['hostname']
		)
		data['signatureMethod'] = "HmacSHA256"
		data['signatureVersion'] = "2"
		
		data['signature'] = self.generateSignature(httpVerb, fpsHost, fpsURI, data)
		
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
	
	# TODO: replace phaseID with transactionID, have a payment / transaction endpoint that creates a new transaction record
	
	def render(self, phaseID):
		accessKey = AmazonS3.getSettingWithTag('key_id')
		secretKey = AmazonS3.getSettingWithTag('key_secret')
		httpVerb = 'POST'
		fpsHost = AmazonS3.getSettingWithTag('simple_pay_host')
		fpsURI = AmazonS3.getSettingWithTag('fps_make_payment_uri')
		
		phase = AgreementPhase.retrieveByID(phaseID)
		agreement = Agreement.retrieveByID(phase['agreementID'])
		vendor = User.retrieveByID(agreement['vendorID'])
		agreementName = (agreement['name']
			if len(agreement['name']) <= 78
			else agreement['name'][:75] + '...'
		)

		email = UserPrefs.retrieveByUserIDAndName(vendor['id'], 'amazon_recipient_email')
		token = UserPrefs.retrieveByUserIDAndName(vendor['id'], 'amazon_token_id')
		
		uniquingAgent = Data(uuid4().get_bytes()).stringWithEncoding(Base58)[:5]
		
		data = OrderedDict()
	
		data['abandonURL'] = '{0}://{1}/agreement/{2}'.format(
			self.request.protocol,
			self.handler.application.configuration['wurkhappy']['hostname'],
			agreement['id']
		) # TODO: Fixme!
		data['accessKey'] = accessKey
		data['amount'] = phase.getCostString('USD ', 'USD 0.00')
		
		if len(phase['description']) > 100:
			data['description'] = phase['description'][:97] + '...'
		else:
			data['description'] = phase['description']
		
		data['immediateReturn'] = 'false'
		data['ipnUrl'] = '{0}://{1}/callbacks/amazon/simplepay/paymentnotification'.format(
			self.request.protocol, self.handler.application.configuration['wurkhappy']['hostname']
		)
		data['processImmediate'] = 'true'
		data['recipientEmail'] = email['value']
		data['referenceId'] = '{0}.{1}'.format(phaseID, uniquingAgent)
		data['returnUrl'] = '{0}://{1}/agreement/{2}'.format(
			self.request.protocol,
			self.handler.application.configuration['wurkhappy']['hostname'],
			agreement['id']
		)
		data['signatureMethod'] = "HmacSHA256"
		data['signatureVersion'] = "2"
		data['variableMarketplaceFee'] = "0"
		data['signature'] = self.generateSignature(httpVerb, fpsHost, fpsURI, data)
		
		return self.render_string(
			"modules/amazon/simplepaybutton.html",
			method=httpVerb,
			action='https://{0}/{1}'.format(fpsHost, fpsURI),
			buttonImageURL='https://images-na.ssl-images-amazon.com/images/G/01/asp/golden_large_paynow_withlogo_darkbg.gif',
			data=data
		)



