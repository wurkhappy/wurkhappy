from __future__ import division
import re

from base import *
from models.user import *
from models.agreement import *
from models.profile import Profile
from helpers import fmt
from tools.orm import ORMJSONEncoder
from tools.beanstalk import Beanstalk

from datetime import datetime
import hashlib
import logging



class AgreementBase(object):
	def assembleDictionary(self, agreement):
		# This should probably go in the model class, but it
		# could be considered controller, so it's here for now.
		
		agreementDict = agreement.publicDict()
		
		client = User.retrieveByID(agreement.clientID) if agreement.clientID else None
		agreementDict["client"] = client and client.publicDict()
		
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

class AgreementListHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def get(self, withWhom):	
		user = self.current_user
		
		templateDict = {
			"_xsrf": self.xsrf_token,
			"userID": user.id
		}
		
		if withWhom.lower() == 'clients':
			agreementType = 'Client'
			agreements = Agreement.iteratorWithVendorID(user.id)
			templateDict['agreementCount'] = Agreement.countWithVendorID(user.id)
			templateDict['aggregateCost'] = "$%.0f" % ((Agreement.amountWithVendorID(user.id) or 0.0) / 100)
		elif withWhom.lower() == 'vendors':
			agreementType = 'Vendor'
			agreements = Agreement.iteratorWithClientID(user.id)
			templateDict['agreementCount']  = Agreement.countWithClientID(user.id)
			templateDict['aggregateCost']  = "$%.0f" % ((Agreement.amountWithClientID(user.id) or 0.0) / 100)
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
				"other_id": usr and usr.id,
				"other_name": usr and usr.getFullName(),
				"date": agr.dateCreated.strftime('%B %d, %Y'),
				"amount": agr.getCostString(),
				"profileURL": usr and (usr.profileSmallURL or '#'), # Default profile photo? Set during signup?
				#"state": InProgressState.currentState(agr),
			})
		
		for agreement in agreements:
			stateClass = agreement.getCurrentState().__class__ # AgreementState.currentState(agreement, []).__class__
			
			if stateClass == 'InvalidState':
				logging.error('Agreement %d (vendor: %d, client: %d) is invalid' % (
						agreement.id, agreement.vendorID, agreement.clientID
					)
				)
			if agreementType == 'Client':
				other = User.retrieveByID(agreement.clientID) if agreement.clientID else None
				
				if stateClass in [DraftState, DeclinedState, ContestedState]:
					appendAgreement(actionItems, agreement, other)
				elif stateClass in [EstimateState, CompletedState]:
					appendAgreement(awaitingReply, agreement, other)
				elif stateClass in [InProgressState]:
					appendAgreement(inProgress, agreement, other)
			else:
				other = User.retrieveByID(agreement.vendorID)
				
				if stateClass in [EstimateState, CompletedState]:
					appendAgreement(actionItems, agreement, other)
				elif stateClass in [DeclinedState, ContestedState]:
					appendAgreement(awaitingReply, agreement, other)
				elif stateClass in [InProgressState]:
					appendAgreement(inProgress, agreement, other)
		
		templateDict['agreementType'] = agreementType
		templateDict['agreementGroups'] = []
		
		for (name, lst) in [
			("Requires Attention", actionItems),
			("Waiting for Client", awaitingReply),
			("In Progress", inProgress)]:
			
			if len(lst):
				templateDict['agreementGroups'].append((name, lst))
		
		title = "%s Agreements &ndash; Wurk Happy" % agreementType
		self.render("agreement/list.html", title=title, bag=templateDict, agreement_with=agreementType)


class AgreementHandler(Authenticated, BaseHandler, AgreementBase):
	def generateActionList(self, agreementState, role, phaseNumber):
		"""
		Given an agreement state and the current user's role, returns a list
		of button actions to be displayed for the agreement. The list has
		zero, one, or two dictionaries which contain values for the button's
		DOM ID, text label, action URL, HTTP method, and request parameters
		for the API call. The Template knows what to do with this info.
		
		The phaseNumber parameter is a way to pass the buck back to the
		AgreementState object that actually knows about this shit.
		"""
		
		# State: {
		# 	"role": {
		# 		"name": "ActionName",
		# 		"action": "/path/to/action.json",
		# 		"params": "key=value"
		# 	}
		# }
		
		state = agreementState.__class__
		agreement = agreementState.agreement
		
		return {
			DraftState : {
				"vendor": [ {
					"id": "action-save",
					"capture-id": "agreement-form",
					"name": "Save Draft",
					"action": "/agreement/%d/update.json" % agreement.id,
					"method": "POST",
					"params": { }
				}, {
					"id": "action-send",
					"capture-id": "agreement-form",
					"name": "Send Estimate",
					"action": "/agreement/%d/send.json" % agreement.id,
					"method": "POST",
					"params": { }
				} ],
				"client": []
			},
			EstimateState : {
				"vendor": [ {
					"id": "action-save",
					"capture-id": "agreement-form",
					"name": "Save Changes",
					"action": "/agreement/%d/update.json" % agreement.id,
					"method": "POST",
					"params": { }
				} ],
				"client": [ {
					"id": "action-accept",
					"capture-id": "comments-form",
					"name": "Accept Estimate",
					"action": "/agreement/%d/accept.json" % agreement.id,
					"method": "POST",
					"params": { }
				}, {
					"id": "action-decline",
					"capture-id": "comments-form",
					"name": "Decline Estimate",
					"action": "/agreement/%d/decline.json" % agreement.id,
					"method": "POST",
					"params": { }
				} ]
			},
			DeclinedState : {
				"vendor": [ {
					"id": "action-save",
					"capture-id": "agreement-form",
					"name": "Save as Draft",
					"action": "/agreement/%d/update.json" % agreement.id,
					"method": "POST",
					"params": { }
				}, {
					"id": "action-resend",
					"capture-id": "agreement-form",
					"name": "Save and Re-submit",
					"action": "/agreement/%d/send.json" % agreement.id,
					"method": "GET",
					"params": { }
				} ],
				"client": []
			},
			InProgressState : {
				"vendor": [ {
					"id": "action-markcomplete",
					"name": "Mark Completed",
					"action": "/agreement/%d/mark_complete.json" % agreement.id,
					"method": "POST",
					"params": { 'phaseNumber': phaseNumber }
					# Generated by the AgreementState
				} ],
				"client": []
			},
			CompletedState : {
				"vendor": [],
				"client": [ {
					"id": "action-verify",
					"name": "Verify and Pay",
					# The verify and pay action should redirect to payment page.
					# But we do this for now to prove it works.
					"action": "/payment/new.json",
					# "action": "/agreement/%d/verify.json" % agreement.id,
					"method": "POST",
					"params": { 'phaseNumber': phaseNumber }
				}, {
					"id": "action-dispute",
					"capture-id": "comments-form",
					"name": "Dispute",
					"action": "/agreement/%d/dispute.json" % agreement.id,
					"method": "POST",
					"params": { 'phaseNumber': phaseNumber }
				} ]
			},
			PaidState : {
				"vendor": [],
				"client": []
			},
			InvalidState : {
				"vendor": [],
				"client": []
			}
		}[state][role]
	
	# @web.authenticated
	# @todo: SECURITY AUDIT
	def get(self, agreementID=None):
		user = self.current_user
		agreement = None
		
		if not user:
			logging.warn(self.request.arguments)
			token = self.get_argument("t", None)
			
			agreement = agreementID and Agreement.retrieveByID(agreementID)
			
			# fingerprint = hashlib.md5(str(token)).hexdigest() # EWWWWW!
			# logging.warn(fingerprint)
			# agreement = token and Agreement.retrieveByFingerprint(fingerprint)
			
			if not (agreement and agreement.tokenIsValid(token)):
				self.set_status(403)
				self.write("forbidden")
				# @todo: Properly handle the case
				return
			
			user = User.retrieveByID(agreement.clientID)
		
		if not agreementID:
			# Must have been routed from /agreement/new
			title = "New Agreement &ndash; Wurk Happy"
			
			empty = {
				"_xsrf": self.xsrf_token,
				"id": None,
				"name": "",
				"date": "",
				"amount": "",
				"summary": "",
				"client": None,
				"vendor": None,
				"phases": [],
				"actions": [ {
					"id": "action-save",
					"capture-id": "agreement-form",
					"name": "Save as Draft",
					"action": "/agreement/new.json",
					"method": "POST",
					"params": { }
				}, {
					"id": "action-send",
					"capture-id": "agreement-form",
					"name": "Send Estimate",
					"action": "/agreement/send.json",
					"method": "POST",
					"params": { }
				} ],
				"self": "vendor"
			}
				
			self.render("agreement/edit.html", title=title, data=empty, json=lambda x: json.dumps(x, cls=ORMJSONEncoder))
			return
		
		agreement = agreement or Agreement.retrieveByID(agreementID)
		phases = list(AgreementPhase.iteratorWithAgreementID(agreement.id))
		
		if not agreement:
			self.set_status(404)
			self.write("Not Found")
			return
		
		if agreement.vendorID == user.id:
			agreementType = 'Client'
		elif agreement.clientID == user.id:
			stateClass = agreement.getCurrentState().__class__ # AgreementState.currentState(agreement, phases).__class__
			
			if stateClass in [DraftState, InvalidState]:
				logging.error('Agreement %d (vendor: %d, client: %d) is invalid' % (
						agreement.id, agreement.vendorID, agreement.clientID
					)
				)
				self.set_status(404)
				self.write("Not found")
				return
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
		#     "id": 123
		#     "name": "Marketing Outline",
		#     "date": "January 1, 2010",
		#     "amount": "$1,300.52",
		#     "client": {
		#         "id": 1,
		#         "fullName": "Cindy Jones",
		#         "profileURL": "http://media.wurkhappy.com/eW5no...s.png"
		#     },
		#     "vendor": {
		#         "id": 17,
		#         "fullName": "Greg Smith",
		#         "profileURL": "http://media.wurkhappy.com/EKveW...s.png"
		#     },
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
		
		templateDict = {
			"_xsrf": self.xsrf_token,
			"id": agreement.id,
			"name": agreement.name,
			"date": agreement.dateCreated.strftime('%B %d, %Y'),
			"amount": agreement.getCostString(),
		}
		
		summary = AgreementSummary.retrieveByAgreementID(agreement.id)
		
		if summary:
			templateDict['summary'] = summary.summary or ''
			templateDict['summaryComments'] = summary.comments or ''
		else:
			templateDict['summary'] = None
			templateDict['summaryComments'] = ''
		
		if agreementType == 'Client':
			client = User.retrieveByID(agreement.clientID) if agreement.clientID else None
			templateDict["client"] = client and client.publicDict()
			templateDict["vendor"] = user.publicDict()
			templateDict["self"] = "vendor"
			templateDict["other"] = "client"
		else:
			vendor = User.retrieveByID(agreement.vendorID)
			templateDict["client"] = user.publicDict()
			templateDict["vendor"] = vendor.publicDict()
			templateDict["self"] = "client"
			templateDict["other"] = "vendor"
		
		
		# Add the agreement phase data to the template dict
		
		currentState = agreement.getCurrentState() # AgreementState.currentState(agreement, phases)
		phaseNumber = currentState.inProgressPhaseNumber
		inProgressPhase = None
		
		templateDict["phases"] = []
		totalAmount = 0
		
		for phase in phases:
			totalAmount += phase.amount if phase.amount else 0
			
			phaseDict = {
				"amount": "$%.02f" % (phase.amount / 100) if phase.amount else "",
				"description": phase.description,
				"estDateCompleted": phase.estDateCompleted.strftime('%B %d, %Y') if phase.estDateCompleted else None,
				"dateCompleted": phase.dateCompleted.strftime('%B %d, %Y') if phase.dateCompleted else None
			}
			
			if phase.comments:
				phaseDict["comments"] = phase.comments
			
			if phase.phaseNumber == phaseNumber:
				inProgressPhase = phase
			
			templateDict["phases"].append(phaseDict)
		
		templateDict["amount"] = "$%.02f" % (totalAmount / 100)
		
		# Transactions are datetime properties of the agreement.
		
		transactions = [{
			"type": "Sent by ",
			"user": "vendor",
			"date": agreement.dateCreated.strftime('%B %d, %Y')
		}]
		
		if agreement.dateDeclined:
			transactions.append({
				"type": "Declined by ",
				"user": "client",
				"date": agreement.dateDeclined.strftime('%B %d, %Y')
			})
		
		if agreement.dateModified:
			transactions.append({
				"type": "Modified by ",
				"user": "vendor",
				"date": agreement.dateModified.strftime('%B %d, %Y')
			})
		
		if agreement.dateAccepted:
			transactions.append({
				"type": "Accepted by ",
				"user": "client",
				"date": agreement.dateAccepted.strftime('%B %d, %Y')
			})
		
		if inProgressPhase and inProgressPhase.dateCompleted:
			transactions.append({
				"type": "Completed by ",
				"user": "vendor",
				"date": inProgressPhase.dateCompleted.strftime('%B %d, %Y')
			})
		
		if inProgressPhase and inProgressPhase.dateVerified:
			transactions.append({
				"type": "Verified and paid by ",
				"user": "client",
				"date": inProgressPhase.dateVerified.strftime('%B %d, %Y')
			})
		
		templateDict['transactions'] = transactions
		
		templateDict['state'] = currentState.__class__.__name__
		templateDict['actions'] = self.generateActionList(currentState, templateDict['self'], phaseNumber)
		
		logging.info(templateDict['actions'])
		logging.info(currentState.__class__.__name__)
		
		title = "%s Agreement: %s &ndash; Wurk Happy" % (agreementType, agreement.name)
		
		if agreement.vendorID == user.id and templateDict['state'] in ['DraftState', 'EstimateState', 'DeclinedState']:
			templateDict['uri'] = self.request.uri
			logging.info(templateDict)
			self.render("agreement/edit.html", title=title, data=templateDict, json=lambda x: json.dumps(x, cls=ORMJSONEncoder))
		else:
			self.render("agreement/detail.html", title=title, data=templateDict, json=lambda x: json.dumps(x, cls=ORMJSONEncoder))



class NewAgreementJSONHandler(Authenticated, BaseHandler, AgreementBase):
	@web.authenticated
	def post(self, action):
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
					('summary', fmt.Enforce(str)),
					('cost', fmt.List(fmt.Currency(None))),
					('details', fmt.List(fmt.Enforce(str))),
					('estDateCompleted', fmt.List(fmt.Enforce(str)))
					# @todo: actually do something with the dates
				]
			)
		except fmt.HTTPErrorBetter as e:
			logging.warn(e.__dict__)
			self.set_status(e.status_code)
			self.write(e.body_content)
			return
		
		agreement.name = args['title']
		
		if args['clientID']:
			client = User.retrieveByID(args['clientID'])
			
			if client and client.id == user.id:
				error = {
					"domain": "application.conflict",
					"display": "You can't send estimates to yourself. Please choose a different client.",
					"debug": "'clientID' parameter has forbidden value"
				}
				self.set_status(409)
				self.renderJSON(error)
				return
			
			if not client:
				error = {
					"domain": "resource.not_found",
					"display": "We couldn't find the client you specified. Could you please try that again?",
					"debug": "the 'clientID' specified was not found"
				}
				self.set_status(400)
				self.renderJSON(error)
				return
		elif args['email']:
			client = User.retrieveByEmail(args['email'])
			
			if client and client.id == user.id:
				error = {
					"domain": "application.conflict",
					"display": "You can't send estimates to yourself. Please choose a different client.",
					"debug": "'clientID' parameter has forbidden value"
				}
				self.set_status(409)
				self.renderJSON(error)
				return
			
			if not client:
				client = User.initWithDict(
					dict(email=args['email'], invitedBy=user.id)
				)
				
				client.save()
				client.refresh()
		else:
			client = None
		
		agreement.clientID = client and client.id
		agreement.save()
		agreement.refresh()
		
		if action == "send":
			if not agreement.clientID:
				# @todo: Check this. I'm pretty sure it makes sense, but uh...
				error = {
					"domain": "application.conflict",
					"display": "You need to choose a recipient in order to send this estimates. Please choose a client in the recipient field.",
					"debug": "'clientID' or 'email' parameter required"
				}
				self.set_status(409)
				self.renderJSON(error)
				return
			
			clientState = UserState.currentState(client)
			
			if isinstance(clientState, InvitedUserState):
				data = {"confirmationHash": "foo"}
				clientState.doTransition("send_verification", data)
				
				with Beanstalk() as bconn:
					msg = json.dumps(dict(
						userID=client.id,
						agreementID=agreement.id,
						action='agreementInvite'
					))
					
					bconn.use('email_notification_queue')
					r = bconn.put(msg)
					logging.info('Beanstalk: email_notification_queue#%d %s' % (r, msg))
			
			agreement.dateSent = datetime.now()
			agreement.save()
			agreement.refresh()
		
		summary = AgreementSummary.initWithDict(dict(agreementID=agreement.id))
		summary.summary = args['summary']
		
		summary.save()
		summary.refresh()
		
		for num, (cost, descr) in enumerate(zip(args['cost'], args['details'])):
			phase = AgreementPhase()
			phase.agreementID = agreement.id
			phase.phaseNumber = num
			phase.amount = cost
			phase.description = descr
			phase.save()
		
		self.set_status(201)
		self.set_header('Location', 'http://' + self.request.host + '/agreement/' + str(agreement.id) + '.json')
		self.renderJSON(self.assembleDictionary(agreement))



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
		
		self.renderJSON(self.assembleDictionary(agreement))



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
			"state": agreement.getCurrentState() # InProgressState.currentState(agreement)
		}
		
		self.renderJSON(stateDict)



class AgreementActionJSONHandler(Authenticated, BaseHandler, AgreementBase):
	
	@web.authenticated
	def post(self, agreementID, action):
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
		
		role = "vendor" if agreement.vendorID == user.id else "client"
		
		logging.info(role)
		logging.info(action)
		
		currentState = agreement.getCurrentState() # AgreementState.currentState(agreement)
		logging.info(currentState.__class__.__name__)
		
		# In order to make sure records are not put in inconsistent states, a
		# list of unsaved records is maintained so records can be saved
		# en masse after a successful state transition. Otherwise, no change
		# occurs.
		
		unsavedRecords = []
		
		# Because of a change to the way we model agreement states (more
		# specifically the transitions between them), we're packing up a data
		# object that gets passed to the performTransition() function.
		
		transitionData = {}
		
		# If role is vendor, make changes to the agreement before modifying
		# the agreement's state. That way, if the state transition is invalid
		# the changes to the agreement record won't be saved.
		
		if role == "vendor":
			try:
				args = fmt.Parser(self.request.arguments,
					optional= [
						('title', fmt.Enforce(str)),
						('email', fmt.Enforce(str)),
						('clientID', fmt.PositiveInteger()),
						('summary', fmt.Enforce(str)),
						('cost', fmt.List(fmt.Currency(None))),
						('details', fmt.List(fmt.Enforce(str))),
						('estDateCompleted', fmt.List(fmt.Enforce(str))),
						('phaseNumber', fmt.Enforce(int))
					]
				)
			except fmt.HTTPErrorBetter as e:
				logging.warn(e.__dict__)
				self.set_status(e.status_code)
				self.write(e.body_content)
				return
			
			if isinstance(currentState, DraftState):
				if args['clientID']:
					client = User.retrieveByID(args['clientID'])
					
					if not client:
						error = {
							"domain": "resource.not_found",
							"display": (
								"We couldn't find the client you specified. "
								"Could you please try that again?"
							),
							"debug": "the 'clientID' specified was not found"
						}
						self.set_status(400)
						self.renderJSON(error)
						return
					
					agreement.clientID = client.id
				elif args['email']:
					client = User.retrieveByEmail(args['email'])
					
					if client and client.id == user.id:
						error = {
							"domain": "application.conflict",
							"display": "You can't send estimates to yourself. Please choose a different client.",
							"debug": "'clientID' parameter has forbidden value"
						}
						self.set_status(409)
						self.renderJSON(error)
						return
					
					if not client:
						client = User.initWithDict(
							dict(email=args['email'],invitedBy=user.id)
						)
						
						client.save()
						client.refresh()
					agreement.clientID = client.id
				
				if action == "send":
					if agreement.clientID is None:
						# @todo: this should be handled in the doTransition method...
						error = {
							"domain": "application.consistency",
							"display": (
								"To send an estimate, you must specify a client. "
								"Please enter a recipient's name or email address."
							),
							"debug": "'clientID' value required to send estimate"
						}
						self.set_status(400)
						self.renderJSON(error)
						return
					else:
						clientState = UserState.currentState(client)
						
						if isinstance(clientState, InvitedUserState):
							data = {"confirmationHash": "foo"}
							clientState.doTransition("send_verification", data)
							
							# @todo: also defer this to after the transition is successful?
							with Beanstalk() as bconn:
								msg = json.dumps(dict(
									userID=client.id,
									agreementID=agreement.id,
									action='agreementInvite'
								))
								
								bconn.use('email_notification_queue')
								r = bconn.put(msg)
								logging.warn('Beanstalk: email_notification_queue#%d %s' % (r, msg))
				elif action == "mark_complete":
					if not args['phaseNumber']:
						error = {
							"domain": "web.request",
							"display": (
								"Something went wrong marking this agreement complete."
							),
							"debug": "missing required 'phaseNumber' parameter"
						}
						self.set_status(400)
						self.renderJSON(error)
					transitionData['phaseNumber'] = args['phaseNumber']
				
			if (isinstance(currentState, DraftState) or 
					isinstance(currentState, EstimateState) or 
					isinstance(currentState, DeclinedState)):
				
				agreement.name = args['title'] or agreement.name
				
				summary = AgreementSummary.retrieveByAgreementID(agreement.id)
				
				if not summary:
					summary = AgreementSummary.initWithDict(
						dict(agreementID=agreement.id)
					)
				
				summary.summary = args['summary'] or summary.summary
				
				# @todo: Defer phase saves until state transition is complete
				for num, (cost, descr) in enumerate(zip(args['cost'], args['details'])):
					phase = AgreementPhase.retrieveByAgreementIDAndPhaseNumber(agreement.id, num)
					
					if not phase:
						phase = AgreementPhase.initWithDict(
							dict(agreementID=agreement.id, phaseNumber=num)
						)
					
					if cost:
						phase.amount = cost
					
					if descr:
						phase.description = descr
					phase.save()
				
				summary.save()
				agreement.save()
		
		
		# Clients can accept or decline an estimate, in which case the comment
		# fields in the agreement summary and agreement phase records get 
		# updated; or they can dispute or verify a completed agreement, in
		# which case the dispute fields in the agreement summary and agreement
		# phase records get updated.
		
		elif role == "client":
			try:
				args = fmt.Parser(self.request.arguments,
					optional=[
						('summaryComments', fmt.Enforce(str)),
						('phaseComments', fmt.List(fmt.Enforce(str))),
						('phaseNumber', fmt.Enforce(int))
					]
				)
			except fmt.HTTPErrorBetter as e:
				logging.warn(e.__dict__)
				self.set_status(e.status_code)
				self.write(e.body_content)
				return
			
			if isinstance(currentState, EstimateState) and action in ["accept", "decline"]:
				agreementSummary = AgreementSummary.retrieveByAgreementID(agreement.id)
				
				if not agreementSummary:
					agreementSummary = AgreementSummary.initWithDict(
						dict(agreementID=agreement.id)
					)
				
				agreementSummary.comments = args['summaryComments']
				agreementSummary.save()
				
				for phase in AgreementPhase.iteratorWithAgreementID(agreement.id):
					if phase.phaseNumber < len(args['phaseComments']):
						phase.comments = args['phaseComments'][phase.phaseNumber]
						phase.save()
			elif isinstance(currentState, CompletedState) and action in ["dispute", "verify"]:
				if not args['phaseNumber']:
					error = {
						"domain": "web.request",
						"display": (
							"Something went wrong marking this agreement complete."
						),
						"debug": "missing required 'phaseNumber' parameter"
					}
					self.set_status(400)
					self.renderJSON(error)
				transitionData['phaseNumber'] = args['phaseNumber']
		
		# currentState = currentState.doTransition(role, action)
		currentState.performTransition(role, action, transitionData)
		# @todo: Return 409 here if state transition fails.
		# @todo: Save records.
		
		self.renderJSON(self.assembleDictionary(agreement))

