from __future__ import division
import re

from base import *
from models.user import User
from models.agreement import *
from models.profile import Profile
from helpers import fmt

from datetime import datetime
import logging



class AgreementBase(object):
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
	
	
	
	def assembleDictionary(self, agreement):
		# This should probably go in the model class, but it
		# could be considered controller, so it's here for now.
		
		agreementDict = agreement.publicDict()
		
		client = User.retrieveByID(agreement.clientID)
		agreementDict['client'] = client.publicDict()
		
		vendor = User.retrieveByID(agreement.vendorID)
		agreementDict['vendor'] = vendor.publicDict()
		
		del(agreementDict['clientID'])
		del(agreementDict['vendorID'])
		
		agreementDict['phases'] = []
		
		for phase in AgreementPhase.iteratorWithAgreementID(agreement.id):
			agreementDict['phases'].append(phase.publicDict())
		
		return agreementDict



# -------------------------------------------------------------------
# Profile (Add / Edit)
# -------------------------------------------------------------------

class AgreementsHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def get(self, withWhom):	
		user = self.current_user
		
		bag = {
			"userID": user.id
		}
		
		if withWhom.lower() == 'clients':
			agreementType = 'Client'
			agrmnts = Agreement.iteratorWithVendorID(user.id)
			bag['agreementCount'] = Agreement.countWithVendorID(user.id)
			bag['aggregateCost'] = "$%.0f" % ((Agreement.amountWithVendorID(user.id) or 0.0) / 100)
		elif withWhom.lower() == 'vendors':
			agreementType = 'Vendor'
			agrmnts = Agreement.iteratorWithClientID(user.id)
			bag['agreementCount']  = Agreement.countWithClientID(user.id)
			bag['aggregateCost']  = "$%.0f" % ((Agreement.amountWithClientID(user.id) or 0.0) / 100)
		else:
			self.set_status(403)
			self.write("Forbidden")
			return
		
		# agreementList = []
		
		actionItems = []
		awaitingReply = []
		inProgress = []
		
		def appendAgreement(lst, agr, usr):
			lst.append({
				"id": agr.id,
				"name": agr.name,
				"other_id": usr.id,
				"other_name": usr.getFullName(),
				"date": agr.dateCreated.strftime('%B %d, %Y'),
				"amount": "$%.02f" % (agr.amount / 100) if agr.amount else "",
				#"state": AgreementState.currentState(agr),
			})
		
		for agrmnt in agrmnts:
			if agreementType == 'Client':
				other = User.retrieveByID(agrmnt.clientID)
				#TODO: use agreement states here
				if agrmnt.dateDeclined or agrmnt.dateContested:
					appendAgreement(actionItems, agrmnt, other)
				elif not agrmnt.dateAccepted:
					appendAgreement(awaitingReply, agrmnt, other)
				else:
					appendAgreement(inProgress, agrmnt, other)
			else:
				appendAgreement(actionItems, agrmnt, User.retrieveByID(agrmnt.vendorID))
		
		bag['agreementType'] = agreementType
		bag['agreementGroups'] = [
			("Requires Attention", actionItems),
			("Waiting for Client", awaitingReply),
			("In Progress", inProgress)
		]
		
		#agreements = [("In Progress", agreementList)]
		title = "%s Agreements &ndash; Wurk Happy" % agreementType
		self.render("agreement/list.html", title=title, bag=bag, agreement_with=agreementType)


class AgreementHandler(Authenticated, BaseHandler, AgreementBase):
	def constructDateTime(self, day, month, year):
		return datetime(int(year), int(month), int(day))
	
	def generateActionList(self, agreementState, role):
		"""Returns an action list
			
			"state": {
				"role": {
					"name": "ActionName",
					"action": "/path/to/action.json",
					"params": "key=value"
				}
			}
		"""
		
		state = agreementState.__class__
		agreement = agreementState.agreementInstance
		
		return {
			DraftState : {
				"vendor": [ {
					"id": "action-send-button",
					"name": "Send Estimate",
					"action": "/agreement/%d/status.json" % agreement.id,
					"method": "POST",
					"params": { "action": "send" }
				} ],
				"client": []
			},
			EstimateState : {
				"vendor": [ {
					"id": "action-edit-button",
					"name": "Edit Estimate",
					"action": "/agreement/%d.json" % agreement.id,
					"method": "GET",
					"params": { "edit": True }
				} ],
				"client": [ {
					"id": "action-accept-button",
					"name": "Accept Estimate",
					"action": "/agreement/%d/status.json" % agreement.id,
					"method": "POST",
					"params": { "action": "accept" }
				}, {
					"id": "action-decline-button",
					"name": "Decline Estimate",
					"action": "/agreement/%d/status.json" % agreement.id,
					"method": "POST",
					"params": { "action": "decline" }
				} ]
			},
			DeclinedState : {
				"vendor": [ {
					"id": "action-resend-button",
					"name": "Edit and Re-send",
					"action": "/agreement/%d.json" % agreement.id,
					"method": "GET",
					"params": { "edit": True }
				} ],
				"client": []
			},
			AgreementState : {
				"vendor": [ {
					"id": "action-markcomplete-button",
					"name": "Mark Completed",
					"action": "/agreement/%d/status.json" % agreement.id,
					"method": "POST",
					"params": { "action": "mark_completed" }
				} ],
				"client": []
			},
			CompletedState : {
				"vendor": [],
				"client": [ {
					"id": "action-verify-button",
					"name": "Verify and Pay",
					# The verify and pay action should redirect to payment page.
					# But we do this for now to prove it works.
					"action": "/agreement/%d/status.json" % agreement.id,
					"method": "POST",
					"params": { "action": "verify" }
				}, {
					"id": "action-dispute-button",
					"name": "Dispute",
					"action": "/agreement/%d/status.json" % agreement.id,
					"method": "POST",
					"params": { "action": "dispute" }
				} ]
			},
			PaidState : {
				"vendor": [],
				"client": []
			}
		}[state][role]
		
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
			
			empty = {
				"id": None,
				"name": "",
				"date": "",
				"amount": "",
				"client": None,
				"vendor": None,
				"phases": [],
				"actions": []
			}
				
			self.render("agreement/edit.html", title=title, agreement_with='Client', bag=empty, date_html=self.constructDateForm(datetime.now()))
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
		
		
		# The agreement data gets wrapped up in a dictionary for
		# the template. This contains name, date, and amount of
		# the agreement, as well as terms, transaction dates, and
		# relationships.
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
		#             "user": "client",
		#             "type": "Sent by ",
		#             "date": "January 1, 2010"
		#         }, {
		#             "user": "vendor",
		#             "type": "Approved by ",
		#             "date": "January 3, 2010"
		#         }],
		#     "phases": [{
		#             "amount": "2,500.00",
		#             "estDateCompleted": "August 1, 2011",
		#             "dateCompleted": "August 1, 2011,
		#             "description": "Lorem ipsum dolor..."
		#         }, {
		#             "amount": "1,500.00",
		#             "estDateCompleted": "August 15, 2011",
		#             "dateCompleted": None,
		#             "description": "Sit amet hoc infinitim...",
		#             "comments": "Bacon mustache fixie PBR..."
		#     }],
		#     "actions": [{
		#             "name": "Accept Agreement",
		#             "action": "/agreement/15/status.json",
		#             "params": "status=accepted"
		#         },{
		#             "name": "Request Changes",
		#             "action": "/agreement/15/status.json",
		#             "params": "status=declined"
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
		
		
		# Add the agreement phase data to the JSON bag
		
		phases = AgreementPhase.iteratorWithAgreementID(agrmnt.id)
		agreement["phases"] = []
		totalAmount = 0
		
		for phase in phases:
			totalAmount += phase.amount if phase.amount else 0
			
			agreement["phases"].append({
				"amount": "$%.02f" % (phase.amount / 100) if phase.amount else "",
				"description": phase.description,
				"estDateCompleted": phase.estDateCompleted.strftime('%B %d, %Y') if phase.estDateCompleted else None,
				"dateCompleted": phase.dateCompleted.strftime('%B %d, %Y') if phase.dateCompleted else None
			})
			
			if phase.comments:
				agreement["phases"]["comments"] = phase.comments
		
		agreement["amount"] = "$%.02f" % (totalAmount / 100)
		
		# Transactions are datetime properties of the agreement.
		
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
		
		if agrmnt.dateCompleted:
			transactions.append({
				"type": "Completed by ",
				"user": "vendor",
				"date": agrmnt.dateCompleted.strftime('%B %d, %Y')
			})
		
		if agrmnt.dateVerified:
			transactions.append({
				"type": "Verified and paid by ",
				"user": "client",
				"date": agrmnt.dateVerified.strftime('%B %d, %Y')
			})
		
		agreement['transactions'] = transactions
		currentState = AgreementStates.currentState(agrmnt)
		agreement['actions'] = self.generateActionList(currentState, agreement['self'])
#self.generateActionList(agrmnt, AgreementState.currentState(agrmnt), agreement['self'])
		
		logging.info(agreement['actions'])
		logging.info(currentState.__class__.__name__)
		
		#TODO: display edit interface depending on agreement state
		if 'edit' in self.request.arguments and self.request.arguments['edit'] == ['true']:
			agreement['uri'] = self.request.uri
			logging.info(agreement)
			title = "Edit Agreement: %s &ndash; Wurk Happy" % (agrmnt.name)
			self.render("agreement/edit.html", title=title, agreement_with=agreementType, bag=agreement, date_html=self.constructDateForm(agrmnt.dateCreated), json=json.dumps)
		else:
			title = "%s Agreement: %s &ndash; Wurk Happy" % (agreementType, agrmnt.name) 
			self.render("agreement/detail.html", title=title, agreement_with=agreementType, bag=agreement, json=json.dumps)
	
	
	@web.authenticated
	def post(self, agreementID=None):
		user = self.current_user
		
		logging.warn(self.request.arguments)
		
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
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('title', fmt.Enforce(str)),
					('cost', fmt.PositiveInteger(0)),
					('details', fmt.Enforce(str)),
					('refund', fmt.Enforce(str))
				],
				required=[]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			logging.warn(e.message)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		if args['title']:
			agreement.name = args['title']
		
		if args['cost']:
			agreement.cost = args['cost']
		
		if agreement.id:
			agreement.dateModified = datetime.now()
		
		logging.warn(agreement.__dict__)
		agreement.save()
		
		if args['details']:
			agreementText = AgreementTxt.retrieveByAgreementID(agreement.id)
		
			if not agreementText:
				agreementText = AgreementTxt.initWithDict(dict(agreementID=agreement.id))
		
			agreementText.agreement = args['details']
		
		if args['refund']:
			agreementText = agreementText or AgreementTxt.retrieveByAgreementID(agreement.id)
			
			if not agreementText:
				agreementText = AgreementTxt.initWithDict(dict(agreementID=agreement.id))
			
			agreementText.refund = args['refund']
		
		if agreementText:
			agreementText.save()
		
		self.redirect('/agreement/%d' % agreement.id)



class NewAgreementJSONHandler(Authenticated, BaseHandler, AgreementBase):
	@web.authenticated
	def post(self):
		user = self.current_user
		
		logging.warn(self.request.arguments)
		
		agreement = Agreement.initWithDict(dict(vendorID=user.id))
		
		agreementText = None
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('title', fmt.Enforce(str)),
					('email', fmt.Enforce(str)),
					('clientID', fmt.PositiveInteger()),
					('cost', fmt.List(fmt.Enforce(str))),
					('details', fmt.List(fmt.Enforce(str))),
					('estDateCompleted', fmt.List(fmt.Enforce(str)))
				]
				# required=[
				# 	('clientID', fmt.PositiveInteger())
				# ]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		agreement.name = args['title']
		agreement.clientID = args['clientID']
		
		agreement.save()
		agreement.refresh()
		
		for (num, cost, descr) in zip(range(0, 4), args['cost'], args['details']):
			phase = AgreementPhase()
			phase.agreementID = agreement.id
			phase.phaseNumber = num
			phase.amount = self.parseAmountString(cost)
			phase.description = descr
			phase.save()
		
		self.set_status(201)
		self.set_header('Location', 'http://' + self.request.host + '/agreement/' + str(agreement.id))
		self.write(json.dumps(self.assembleDictionary(agreement)))



class AgreementJSONHandler(Authenticated, BaseHandler, AgreementBase):
	
	@web.authenticated
	def get(self, agreementID):
		user = self.current_user
		
		agreement = Agreement.retrieveByID(agreementID)
		
		if not agreement:
			self.set_status(404)
			self.write('{"success": false}')
			return
		
		if agreement.vendorID != user.id and agreement.clientID != user.id:
			self.set_status(403)
			self.write('{"success": false}')
			return
		
		self.write(json.dumps(self.assembleDictionary(agreement)))
	
	@web.authenticated
	def post(self, agreementID):
		user = self.current_user
		
		agreement = Agreement.retrieveByID(agreementID)
		
		if not agreement:
			self.set_status(404)
			self.write('{"success": false}')
			return
		
		if agreement.vendorID != user.id:
			self.set_status(403)
			self.write('{"success": false}')
			return
		
		agreementText = None
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('title', fmt.Enforce(str)),
					('cost', fmt.Enforce(str)),
					('details', fmt.Enforce(str)),
					('refund', fmt.Enforce(str)),
					('clientID', fmt.PositiveInteger())
				],
				required=[]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		if args['title']:
			agreement.name = args['title']
		
		if args['cost']:
			agreement.cost = self.parseAmountString(args['cost'])
		
		if agreement.id:
			agreement.dateModified = datetime.now()
		
		agreement.save()
		
		if args['details']:
			agreementText = AgreementTxt.retrieveByAgreementID(agreement.id)
		
			if not agreementText:
				agreementText = AgreementTxt.initWithDict(dict(agreementID=agreement.id))
		
			agreementText.agreement = args['details']
		
		if args['refund']:
			agreementText = agreementText or AgreementTxt.retrieveByAgreementID(agreement.id)
			
			if not agreementText:
				agreementText = AgreementTxt.initWithDict(dict(agreementID=agreement.id))
			
			agreementText.refund = args['refund']
		
		if agreementText:
			agreementText.save()
		
		self.write(json.dumps(self.assembleDictionary(agreement)))
		
class AgreementStatusJSONHandler(Authenticated, BaseHandler, AgreementBase):
	
	@web.authenticated
	def get(self, agreementID):
		user = self.current_user
		
		agreement = Agreement.retrieveByID(agreementID)
		
		if not agreement:
			self.set_status(404)
			self.write('{"success": false}')
			return
		
		if agreement.vendorID != user.id and agreement.clientID != user.id:
			self.set_status(403)
			self.write('{"success": false}')
			return
		
		stateDict = {
			"agreement": {
				"id": agreement.id
			},
			"state": AgreementState.currentState(agreement)
		}
		
		self.write(json.dumps(stateDict))
	
	@web.authenticated
	def post(self, agreementID):
		user = self.current_user
		
		agreement = Agreement.retrieveByID(agreementID)
		
		if not agreement:
			self.set_status(404)
			self.write('{"success": false}')
			return
		
		if agreement.vendorID != user.id and agreement.clientID != user.id:
			self.set_status(403)
			self.write('{"success": false}')
			return
		
		agreementText = None
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[],
				required=[
					('action', fmt.StringInSet(AgreementStates.transitionNames))
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		role = "vendor" if agreement.vendorID == user.id else "client"
		logging.info(role)
		logging.info(args['action'])
		currentState = AgreementStates.currentState(agreement)
		logging.info(currentState.__class__.__name__)
		currentState = currentState.doTransition(role, args['action'])
		
		stateDict = {
			"agreement": {
				"id": agreement.id
			},
			"state": currentState.__class__.__name__
		}
		
		self.write(json.dumps(stateDict))
