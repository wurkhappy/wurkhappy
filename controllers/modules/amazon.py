from tornado.web import UIModule
from controllers.orm import ORMJSONEncoder
from controllers.data import Data, Base64

import json
import logging
from datetime import datetime
from hashlib import sha1
from collections import OrderedDict
import hmac
import urllib


class Amazon(object):
	def generateSignature(self, httpVerb, host, uri, data, key):
		'''Generate an Amazon FPS signature for an API request or button form.
		More information can be found at the following URL:
		http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/Sig2CreateSignature.html
		'''
		
		canonicalData = OrderedDict()
		
		for k in sorted(data.keys()):
			canonicalData[urllib.quote(k, '~')] = urllib.quote(data[k], '~')
		
		canonicalString = '&'.join('{0}={1}'.format(k, v) for k, v in canonicalData.iteritems())
		
		plaintext = '{0}\n{1}\n{2}\n{3}'.format(
			httpVerb,
			host.lower(),
			'/{0}'.format(uri),
			canonicalString
		)
		
		hashObj = hmac.new(key, plaintext, sha1)
		data = Data(hashObj.digest())
		return data.stringWithEncoding(Base64)
		

class AcceptMarketplaceFeeButton(UIModule, Amazon):
	""" Presents an HTML form to initiate the vendor's acceptance of Amazon's
	marketplace fees and terms and conditions. Documentation at the following URL:
	http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/marketplace-fee-input.html
	"""
	
	def render(self, vendor, amazon):
		accessKey = amazon['key_id']
		secretKey = amazon['key_secret']
		httpVerb = 'GET'
		host = 'authorize.payments.amazon.com' # amazon['fps_host']
		uri = 'cobranded-ui/actions/start' # amazon['fps_accept_fee_uri']
		
		data = OrderedDict()
		
		data['accessKey'] = accessKey
		# data['callerReference'] = "Some kind of transaction UID"
		data['maxVariableFee'] = "1.00"
		data['pipelineName'] = "Recipient"
		data['recipientPaysFee'] = "false"
		data['returnURL'] = 'http://foo.bar/baz' # TODO: Fixme!
		data['signatureMethod'] = "HmacSHA1"
		data['signatureVersion'] = "2"
		
		data['signature'] = self.generateSignature(httpVerb, host, uri, data, secretKey)
		
		return self.render_string(
			"modules/amazon/simplepaybutton.html",
			method=httpVerb,
			action='https://{0}/{1}'.format(host, uri),
			buttonImageURL='http://g-ecx.images-amazon.com/images/G/01/asp/MarketPlaceFeeWithLogo.gif',
			data=data
		)



class PayWithSimplePayButton(UIModule):
	def render(self, phase, amazon):
		accessKey = amazon['key_id']
		secretKey = amazon['key_secret']
		httpVerb = 'POST'
		host = 'authorize.payments.amazon.com' # amazon['fps_host']
		uri = 'pba/paypipeline' # amazon['fps_make_payment_uri']
		
		data = OrderedDict()
		
		data['abandonURL'] = 'http://foo.bar/baz' # TODO: Fixme!
		data['accessKey'] = accessKey
		data['amount'] = 'USD {0}'.format(phase['amount']) # TODO: Fixme!
		data['description'] = phase['description'] #!
		# data['immediateReturn'] = '1'
		data['ipnUrl'] = 'http://foo.bar/baz' #!
		data['recipientEmail'] = vendor['email']
		data['returnUrl'] = 'http://foo.bar/baz' #!
		data['signatureMethod'] = "HmacSHA1"
		data['signatureVersion'] = "2"
		data['variableMarketplaceFee'] = "1.00"
		
		data['signature'] = self.generateSignature(httpVerb, host, uri, data, secretKey)
		
		return self.render_string(
			"modules/amazon/simplepaybutton.html",
			method=httpVerb,
			action='https://{0}/{1}'.format(host, uri),
			buttonImageURL='',
			data=data
		)
	

