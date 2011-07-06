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
				"amount": "$%.02f" % (agrmnt.amount / 100) if agrmnt.amount else ""
			})
		
		agreements = [("In Progress", agreementList)]
		title = "%s Agreements &ndash; Wurk Happy" % agreementType
		self.render("agreement/list.html", title=title, agreement_with=agreementType, count=count, total=total, agreement_groups=agreements)


class AgreementHandler(Authenticated, BaseHandler):
	def parseAmountString(self, string):
		r = re.compile(r'\$?([0-9,]+)(?:\.([0-9]{2}))?')
		m = r.match(string)
		logging.warn(string)
		if not m or len(m.groups()) != 2:
			return None
		logging.warn(m.groups())
		d = int(m.groups()[0].replace(',', '')) * 100
		
		if m.groups()[1]:
			d += int(m.groups()[1])
		
		return d
	
	def constructDateTime(self, day, month, year):
		return atetime(int(year), int(month), int(day))
	
	@staticmethod
	def constructDateForm(datestamp):
		# Should probably be somewhere else
		months = [
			('January', 1),
			('February', 2),
			('March', 3),
			('April', 4),
			('May', 5),
			('June', 6),
			('July', 7),
			('August', 8),
			('September', 9),
			('October', 10),
			('November', 11),
			('December', 12)
		]
		
		html = '<select name="month" id="">'
		
		for month, num in months:
			selected = ' selected="true"' if datestamp.month == num else ''
			html += '\t<option value="%d"%s>%s</option>' % (num, selected, month)
		
		html += '</select>\n<select name="day" id="">'
		
		for day in range(1, 32):
			selected = ' selected="true"' if datestamp.day == day else ''
			html += '\t<option value="%d"%s>%s</option>' % (day, selected, day)
			
		html += '</select>\n<select name="year" id="">'
		
		for year in range(2011, 2013):
			selected = ' selected="true"' if datestamp.year == year else ''
			html += '\t<option value="%d"%s>%s</option>' % (year, selected, year)
		
		html += '</select>'
		return html
	
	@web.authenticated
	def get(self, agreementID=None):
		user = self.current_user
		
		if not agreementID:
			# Must have been routed from /agreement/new
			title = "New Agreement &ndash; Wurk Happy"
			self.render("agreement/edit.html", title=title, agreement_with='Client', bag=None, date_html=self.constructDateForm(datetime.now()))
			return
		
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
		
		
		# The agreement data gets wrapped up in a bag of JSON. This
		# contains name, date, and amount of the agreement, as well as
		# terms, transaction dates, and relationships.
		# 
		# {
		#     "name": "Marketing Outline",
		#     "date": "January 1, 2010",
		#     "amount": "$1,300.52",
		#     "client": {
		#         "id": 1,
		#         "name": "Cindy Jones" },
		#     "vendor": {
		#         "id": 17,
		#         "name": "Greg Smith" },
		#     "self": "client",
		#     "other": "vendor",
		#     "transactions": [{
		#         "user": "client",
		#         "type": "Sent by ",
		#         "date": "January 1, 2010"
		#     }, {
		#         "user": "vendor",
		#         "type": "Approved by ",
		#         "date": "January 3, 2010"
		#     }]
		# }
		
		agreement = {
			"id": agrmnt.id,
			"name": agrmnt.name,
			"date": agrmnt.dateCreated.strftime('%B %d, %Y'),
			"amount": "$%.02f" % (agrmnt.amount / 100) if agrmnt.amount else ""
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
		
		
		# Add the agreement text and the comment text to the JSON bag
		
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
		
		
		# Transactions are datetime properties of the agreement. They
		
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
		
		agreement['transactions'] = transactions
		
		logging.info(self.request.arguments)
		
		if 'edit' in self.request.arguments and self.request.arguments['edit'] == ['true']:
			agreement['uri'] = self.request.uri
			title = "Edit Agreement: %s &ndash; Wurk Happy" % (agrmnt.name)
			self.render("agreement/edit.html", title=title, agreement_with=agreementType, bag=agreement, date_html=self.constructDateForm(agrmnt.dateCreated))
		else:
			title = "%s Agreement: %s &ndash; Wurk Happy" % (agreementType, agrmnt.name) 
			self.render("agreement/detail.html", title=title, agreement_with=agreementType, bag=agreement)
	
	
	@web.authenticated
	def post(self, agreementID=None):
		user = self.current_user
		
		agreement = Agreement.retrieveByID(agreementID) if agreementID else Agreement()
		
		if not agreement:
			# Should we serve a 404 page?
			self.redirect(self.request.uri)
			return
		
		if not agreement.id:
			agreement.vendorID = user.id
			agreement.clientID = 2
		
		if agreement.vendorID != user.id:
			# Likewise, should we serve a "beat it, jerk" page?
			self.redirect(self.request.uri)
			return
		
		agreementText = None
		
		if 'title' in self.request.arguments:
			agreement.name = self.request.arguments['title'][0]
		
		if 'cost' in self.request.arguments:
			agreement.amount = self.parseAmountString(self.request.arguments['cost'][0])
			pass
		
		if agreement.id:
			agreement.dateModified = datetime.now()
		
		logging.warn(agreement.__dict__)
		agreement.save()
		
		if 'details' in self.request.arguments:
			agreementText = AgreementTxt.retrieveByAgreementID(agreement.id)
			
			if not agreementText:
				agreementText = AgreementTxt.initWithDict(dict(agreementID=agreement.id))
			
			agreementText.agreement = self.request.arguments['details'][0]
		
		if 'refund' in self.request.arguments:
			agreementText = agreementText or AgreementTxt.retrieveByAgreementID(agreement.id)
			
			if not agreementText:
				agreementText = AgreementTxt.initWithDict(dict(agreementID=agreement.id))
			
			agreementText.refund = self.request.arguments['refund'][0]
		
		agreementText.save()
		
		self.redirect('/agreement/%d' % agreement.id)
	
