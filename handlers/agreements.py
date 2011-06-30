from __future__ import division
import re

from base import *
from models.user import User
from models.agreement import *
from models.profile import Profile

from datetime import datetime
import logging

# -------------------------------------------------------------------
# Profile (Add / Edit)
# -------------------------------------------------------------------

class AgreementsHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def get(self, withWhom):	
		user = self.current_user
		
		if withWhom.lower() == 'clients':
			agreementType = 'Client'
			agrmnts = Agreement.iteratorWithVendorID(user.id)
			count = Agreement.countWithVendorID(user.id)
			total = "$%.0f" % (Agreement.amountWithVendorID(user.id) / 100)
		elif withWhom.lower() == 'vendors':
			agreementType = 'Vendor'
			agrmnts = Agreement.iteratorWithClientID(user.id)
			count = Agreement.countWithClientID(user.id)
			total = "$%.0f" % (Agreement.amountWithClientID(user.id) / 100)
		else:
			self.set_status(403)
			self.write("Forbidden")
			return
		
		agreementList = []
		
		for agrmnt in agrmnts:
			if agreementType == 'Client':
				other = User.retrieveByID(agrmnt.clientID)
			else:
				other = User.retrieveByID(agrmnt.vendorID)
			
			agreementList.append({
				"id": agrmnt.id,
				"name": agrmnt.name,
				"other_id": other.id,
				"other_name": other.getFullName(),
				"date": agrmnt.dateCreated.strftime('%B %d, %Y'),
				"amount": "$%.02f" % (agrmnt.amount / 100)
			})
		
		agreements = [("In Progress", agreementList)]
		title = "%s Agreements &ndash; Wurk Happy" % agreementType
		self.render("agreement/list.html", title=title, agreement_with=agreementType, count=count, total=total, agreement_groups=agreements)


class AgreementHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def get(self, agreementID):
		user = self.current_user
		
		agrmnt = Agreement.retrieveByID(agreementID)
		
		if not agrmnt:
			self.set_status(404)
			self.write("Not Found")
			return
		
		if agrmnt.vendorID == user.id:
			agreementType = 'Client'
		elif agrmnt.clientID == user.id:
			agreementType = 'Vendor'
		else:
			self.set_status(403)
			self.write("Forbidden")
			return
		
		agreement = {
			"name": agrmnt.name,
			"date": agrmnt.dateCreated.strftime('%B %d, %Y'),
			"amount": "$%.02f" % (agrmnt.amount / 100)
		}
		
		if agreementType == 'Client':
			client = User.retrieveByID(agrmnt.clientID)
			agreement["client"] = {
				"id": client.id,
				"name": client.getFullName()
			}
			agreement["vendor"] = {
				"id": user.id,
				"name": user.getFullName()
			}
			agreement["self"] = "vendor"
			agreement["other"] = "client"
		else:
			vendor = User.retrieveByID(agrmnt.vendorID)
			agreement["client"] = {
				"id": user.id,
				"name": user.getFullName()
			}
			agreement["vendor"] = {
				"id": vendor.id,
				"name": vendor.getFullName()
			}
			agreement["self"] = "client"
			agreement["other"] = "vendor"
		
		text = AgreementTxt.retrieveByAgreementID(agrmnt.id)
		
		if text:
			agreement["text"] = {
				"agreement": text.agreement,
				"refund": text.refund
			}
		
		comment = AgreementComment.retrieveByAgreementID(agrmnt.id)
		
		if comment:
			agreement["comment"] = {
				"agreement": comment.agreement,
				"refund": comment.refund
			}
		
		
		transactions = [{
			"type": "Sent by ",
			"user": "vendor",
			"date": agrmnt.dateCreated.strftime('%B %d, %Y')
		}]
		
		if agrmnt.dateDeclined:
			transactions.append({
				"type": "Declined by ",
				"user": "client",
				"date": agrmnt.dateDeclined.strftime('%B %d, %Y')
			})
		
		if agrmnt.dateModified:
			transactions.append({
				"type": "Modified by ",
				"user": "vendor",
				"date": agrmnt.dateModified.strftime('%B %d, %Y')
			})
		
		if agrmnt.dateAccepted:
			transactions.append({
				"type": "Accepted by ",
				"user": "client",
				"date": agrmnt.dateAccepted.strftime('%B %d, %Y')
			})
		
		if agrmnt.dateVerified:
			transactions.append({
				"type": "Verified by ",
				"user": "vendor",
				"date": agrmnt.dateVerified.strftime('%B %d, %Y')
			})
		
		title = "%s Agreement: %s &ndash; Wurk Happy" % (agreementType, agrmnt.name) 
		self.render("agreement/detail.html", title=title, agreement_with=agreementType, bag=agreement, transactions=transactions)
		