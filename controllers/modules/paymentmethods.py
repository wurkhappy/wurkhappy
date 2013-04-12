from tornado.web import UIModule
from controllers.orm import ORMJSONEncoder
from controllers.data import Data, Base64, Base58

from models.user import User
from models.paymentmethod import (
	UserPayment, PaymentBase, AmazonPaymentMethod, ZipmarkPaymentMethod
)

from textwrap import dedent
from collections import OrderedDict
import logging
import json



# class ZZZButton(UIModule, AmazonFPS):
# 	'''Presents an HTML form to initiate the vendor's acceptance of Amazon's
# 	marketplace fees and terms and conditions. Documentation at the following URL:
# 	http://docs.amazonwebservices.com/AmazonSimplePay/latest/ASPAdvancedUserGuide/marketplace-fee-input.html
# 	'''
# 	
# 	def render(self, vendorID):
# 		pass

class ButtonMakeDefaultPaymentMethod(UIModule):
	'''Presents an HTML button to make the specified payment method the default one.'''

	def embedded_javascript(self):
		return '''// Button action to make payment method default
		buttonActions['pm_make_default'] = {
			default: function (self, evt) {
				var $source = $(evt.target),
					pmID = $source.closest('span.payment-item').attr('data-payment-method-id'),
					data = {
						paymentMethodID: pmID,
						_xsrf: slug['_xsrf']
					},
					url = '/user/me/paymentmethod/default.json';

				$.ajax({
					url: url,
					data: data,
					type: 'POST',
					dataType: 'json'
				}).then(function (xhr, data) {
					// Update the DOM to reflect a successful change
					// to the default payment method.
					// (1) Get button (2) Replace button with text
					// (3) Get the button's parent's sibling (4) Find
					// the container (5) Put the button in the container

					var $actionButton = $source.closest('ul.action-button'),
						$enclosingDiv = $actionButton.closest('span.payment-item').parent();

					$actionButton.detach();
					$enclosingDiv.siblings('div.column-one-half').first()
						.find('p.payment-method-default-switch').empty().append($actionButton);
					$enclosingDiv.find('p.payment-method-default-switch').html(
						'This payment method will be used for any new payments.'
					);

					$source.removeClass('disabled');
					self.state = 'default';

				}, function (xhr, status, error) {
					alert(
						'There was a problem processing your request. ' +
						"It's most likely temporary, so please " + 
						'try again in a moment.'
					);

					// Enable the button
					$source.removeClass('disabled');
					self.state = 'default';
					
					// throw('API Error: ' + error);
				});

				// Disable the button.
				$source.addClass('disabled');
				self.state = 'disabled';

				return evt.preventDefault();
			},
			disabled: function (self, evt) {
				return evt.preventDefault();
			}
		};
		
		'''

	def render(self):
		return '''<ul class="action-button" style="width:200px;margin-left:auto;">
			<li><a href="#" rel="nofollow" id="pm_make_default" class="top js-button">Make Default</a></li>
		</ul>'''



class PaymentMethodSetup(UIModule):
	'''Presents an HTML interface to configure new payment methods or to edit
	account settings for existing payment methods.'''

	def render(self, user):
		# We build this manually. Only two payment methods for now,
		# so we hard-code the standard payment method info, and add
		# the user's configured payment methods, if any.
		
		paymentMethods = [{
			"class": ZipmarkPaymentMethod,
			"displayName": "Zipmark",
			"title": "Accept Payments via Next-Day Bank Transfer",
			"about": dedent('''Allow your clients to pay via bank-to-bank
				transfer. Wurk Happy charges 1.5% per transaction,
				with a $15 cap.'''),
			"iconURL": "https://zipmark.com/assets/logo-483cefa185e61ccff00342f1d7059b4c.png"
		}, {
			"class": AmazonPaymentMethod,
			"displayName": "Amazon Payments",
			"title": "Accept Payments via Credit Card",
			"about": dedent('''Allow your clients to pay with a credit card.
				Wurk Happy charges 5% per transaction for credit card
				payments.'''),
			"iconURL": "https://payments.amazon.com/img/AP-HLogo-215x35.jpg"
		}] 

		for i, c in enumerate(paymentMethods):
			# YUCK!
			klz = c['class']
			paymentMethod = klz.retrieveByUserID(user['id'])

			if paymentMethod:
				userPayment = UserPayment.retrieveByPMIDAndPMTable(paymentMethod['id'], klz.tableName)
				paymentMethod.userPaymentID = userPayment['id']

				if userPayment['isDefault']:
					paymentMethod.isDefault = True
				else:
					paymentMethod.isDefault = False
					
			paymentMethods[i]['account'] = paymentMethod
		
		return self.render_string(
			'modules/paymentmethod/settings.html',
			paymentMethods=paymentMethods,
			userID=user['id']
		)

