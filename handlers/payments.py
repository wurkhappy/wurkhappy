from __future__ import division

from base import *
from models.user import User, UserPrefs

from helpers import fmt

import json
import logging
import os



# -------------------------------------------------------------------
# PaymentHandler
# -------------------------------------------------------------------

class PaymentHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def get(self):
		user = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('password', fmt.Enforce(str)),
					('phaseID', fmt.Enforce(int)),
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		if not (user and user.passwordIsValid(args['password'])):
			# User wasn't found, or password is wrong, display error
			# @todo: Exponential back-off when user enters incorrect password.
			# @todo: Flag accounds if incorrect password is presented too often.
			error = {
				"domain": "web.request",
				"debug": "please validate authentication credentials"
			}
			self.set_status(401)
			self.renderJSON(error)
			return
		
		phase = AgreementPhase.retrieveByID(args['phaseID'])
		
		if not phase:
			error = {
				"domain": "web.request",
				"debug": "no such phase"
			}
			self.set_status(404)
			self.renderJSON(error)
			return
		
		agreement = Agreement.retrieveByID(phase.agreementID)
		
		if not (agreement and agreement.clientID == user.id):
			# The logged-in user is not authorized to make a payment
			# on this agreement. I don't know how it's even possible
			# to get to this point.
			error = {
				"domain": "application.not_authorized",
				"debug": "I'm sorry Dave, I can't do that"
			}
			self.set_status(403)
			self.renderJSON(error)
			return
		
		# Look up the user's preferred payment method
		paymentPref = UserPrefs.retrieveByUserIDAndName(user.id, 'preferredPaymentID')
		
		if paymentPref:
			paymentMethod = PaymentMethod.retrieveByID(paymentPref.value)
		else:
			paymentMethod = PaymentMethod.retrieveCCMethodWithUserID(user.id)
		
		if not paymentMethod:
			self.set_status(400)
			self.write('boo')
			# @todo: actually handle this error
			return
		
		transaction = Transaction.initWithDict(dict(
			agreementPhaseID=phase.id,
			senderID=user.id,
			recipientID=agreement.vendorID,
			paymentMethodID=paymentMethod.id,
			amount=phase.amount
		))
		
		transaction.save()
		transaction.refresh()
		
		# @todo: Put the transaction info on the processing queue.
		
		transactionJSON = transaction.publicDict()
		transactionJSON['paymentMethod'] = paymentMethod.publicDict()
		del(transactionJSON['paymentMethodID'])
		
		self.renderJSON(transactionJSON)
		