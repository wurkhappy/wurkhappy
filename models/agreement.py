from tools.orm import *
from profile import Profile
from collections import OrderedDict

# -------------------------------------------------------------------
# Agreements
# -------------------------------------------------------------------

class Agreement(MappedObj):
	
	def __init__(self):
		self.id = None
		self.vendorID = None
		self.clientID = None
		self.name = None
		# self.amount = None
		self.dateCreated = None
		self.dateSent = None
		self.dateAccepted = None
		self.dateModified = None
		self.dateDeclined = None
		self.dateVerified = None
		self.dateContested = None
	
	@classmethod
	def tableName(clz):
		return "agreement"
	
	@classmethod
	def countWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT COUNT(*) FROM %s WHERE vendorID = %%s" % clz.tableName(), vendorID)
			result = cursor.fetchone()
			return result['COUNT(*)']
	
	@classmethod
	def countWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT COUNT(*) FROM %s WHERE clientID = %%s" % clz.tableName(), clientID)
			result = cursor.fetchone()
			return result['COUNT(*)']
	
	@classmethod
	def amountWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT SUM(a.amount) FROM %s AS a LEFT JOIN agreementPhase AS b ON b.agreementID = a.id WHERE a.vendorID = %%s AND a.dateAccepted IS NOT NULL AND a.dateVerified IS NULL" % clz.tableName(), vendorID)
			result = cursor.fetchone()
			return result['SUM(a.amount)']
	
	@classmethod
	def amountWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT SUM(a.amount) FROM %s AS a LEFT JOIN agreementPhase AS b ON b.agreementID = a.id WHERE a.clientID = %%s AND a.dateAccepted IS NOT NULL AND a.dateVerified IS NULL" % clz.tableName(), clientID)
			result = cursor.fetchone()
			return result['SUM(a.amount)']
	
	@classmethod
	def iteratorWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE vendorID = %%s" % clz.tableName(), vendorID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()		
	
	@classmethod
	def iteratorWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE clientID = %%s" % clz.tableName(), clientID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	def publicDict(self):
		return OrderedDict([
			('id', self.id),
			('vendorID', self.vendorID),
			('clientID', self.clientID),
			('name', self.name),
			('dateCreated', self.dateCreated.strftime("%Y-%m-%dT%H:%M:%SZ")),
			('dateSent', self.dateSent.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateSent else None),
			('dateAccepted', self.dateAccepted.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateAccepted else None),
			('dateModified', self.dateModified.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateModified else None),
			('dateDeclined', self.dateDeclined.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateDeclined else None),
			('dateVerified', self.dateVerified.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateVerified else None),
			('dateContested', self.dateContested.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateContested else None)
		])


# -------------------------------------------------------------------
# Agreement Text
# -------------------------------------------------------------------

class AgreementTxt (MappedObj):
	
	def __init__(self):
		self.id = None
		self.agreementID = None
		self.agreement = None
		self.refund = None
		self.dateCreated = None
	
	@classmethod
	def tableName(clz):
		return "agreementTxt"
	
	@classmethod
	def retrieveByAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE agreementID = %%s" % clz.tableName(), agreementID)
			result = cursor.fetchone()
			return clz.initWithDict(result)



# -------------------------------------------------------------------
# Agreement Phase
# -------------------------------------------------------------------

class AgreementPhase (MappedObj):
	
	def __init__(self):
		self.id = None
		self.agreementID = None
		self.phaseNumber = None
		self.amount = None
		self.estDateCompleted = None
		self.dateCompleted = None
		self.description = None
		self.comments = None
	
	@classmethod
	def tableName(clz):
		return "agreementPhase"
	
	@classmethod
	def iteratorWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE agreementID = %%s ORDER BY phaseNumber" % clz.tableName(), agreementID)
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	def publicDict(self):
		return OrderedDict([
			('amount', self.amount),
			('estimatedCompletion', self.estDateCompleted),
			('dateCompleted', self.dateCompleted),
			('description', self.description),
			('comments', self.comments)
		])


# -------------------------------------------------------------------
# Agreement Comment
# -------------------------------------------------------------------

class AgreementComment (MappedObj):
	
	def __init__(self):
		self.id = None
		self.agreementID = None
		self.agreement = None
		self.refund = None
		self.dateCreated = None
	
	@classmethod
	def tableName(clz):
		return "agreementComment"
	
	@classmethod
	def retrieveByAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE agreementID = %%s" % clz.tableName(), agreementID)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	

	
# -------------------------------------------------------------------
# Add agreement state -> button stuff
# DraftState -> agreement.dateSent null
#  vendor sees draft, edit (?) and send buttons; send updates dateSent
#  client sees nothing
# EstimateState -> dateSent not null and dateAccepted null and (dateDeclined null or (dateDeclined < dateSent))
#  vendor sees estimate, edit buttons
#  client sees estimate, accept and decline buttons; accept updates dateAccepted; decline updates dateDeclined
# DeclinedState -> dateAccepted null and dateDecline > dateSent
#  vendor sees estimate, edit and re-send buttons; re-sent updates dateSent
#  client sees nothing ?
# AgreementState -> (dateAccepted > dateSent and dateContested null) or (dateContested > dateSent > dateAccepted)
#  vendor sees agreement, mark-completed buttons; mark-completed updates dateSent
#  client sees agreement
# CompletedState -> (dateSent > dateAccepted and dateContested null) or (dateSent > dateContested > dateAccepted)
#  vendor sees agreement
#  client sees agreement, dispute and verify buttons; dispute updates dateContested; verify updates dateVerified
# PaidState -> dateVerified is not null 
#  what to show?
# Do we store elsewhere a history of edits?
# -------------------------------------------------------------------


class AgreementStates(object):
	""" AgreementState """

	def __init__(self, agreementInstance):
		assert type(agreementInstance)==Agreement
		from datetime import datetime
		self.agreementInstance=agreementInstance
		def update_datetime(colName):
			return "UPDATE agreement SET %s = '%s' WHERE id=%d" \
			    % (colName
			       , datetime.strftime(datetime.now(), '%Y-%M-%d %H:%M:%S')
			       , agreementInstance.publicDict()['id'])
		def action_assoc(symbol, name, db_action=None):
			return {"symbol" : symbol, "name" : name, "db_action" : db_action}
		# consider changing this to a comprehension
		self._button_action_map = {"send" : action_assoc("send", "Send Estimate", update_datetime('dateSent'))
					   , "resend" : action_assoc("resend", "Resend Estimate", update_datetime('dateSent'))
					   , "edit" : action_assoc("edit", "Edit Estimate")
					   , "accept" : action_assoc("accept", "Accept Estimate", update_datetime('dateAccepted'))
					   , "decline": action_assoc("decline", "Decline Estimate", update_datetime('dateDeclined'))
					   , "mark_completed" : action_assoc("mark_complete", "Mark Complete", update_datetime('dateSent'))
					   , "dispute" : action_assoc("dispute", "Dispute", update_datetime('dateContested'))
					   , "verify" : action_assoc("verify", "Verify", update_datetime('dateVerified'))}
		self._buttons = {"vendor": [{}], "client" : [{}]}

	# Should change asserts to exceptions later
	def getButtons(self, vendorOrClient=None):
		assert vendorOrClient
		return self._buttons[vendorOrClient]

	def setButtons(self, buttonList, vendorOrClient=None):
		assert vendorOrClient
		self._buttons[vendorOrClient]=[self._button_action_map[b] for b in buttonList]
		# {'vendor' : {"send" : {"name" : "send", "text" : "Send Estimate", "db_action" : "SELECT ..."}} ...

	def addActions(self, actionMap, button, vendorOrClient=None):
		assert vendorOrClient
		index = [i for (i, data) in enumerate(self._buttons[vendorOrClient]) if data['symbol'] == button][0]
		self._buttons[vendorOrClient][index].update(actionMap)
		
	def addFormActions(self, action, method, params):
		""" Special Utility function for adding this specific map. Macro-esque? """
		return {"action" : action, "method" : method, "params" : params}

	@classmethod
	def currentState(clz, agreementInstance):
		""" currentState : Agreement -> AgreementState """

		agreementDict = agreementInstance.publicDict()
		
		dateVerified = agreementDict["dateVerified"]
		dateSent =  agreementDict["dateSent"]
		dateContested = agreementDict["dateContested"]
		dateAccepted = agreementDict["dateAccepted"]
		dateDeclined = agreementDict["dateDeclined"]
		
		states = [('PaidState', dateVerified)
			  ,('DraftState', not dateSent)
			  ,('EstimateState', not dateContested and not dateAccepted and (not dateDeclined or dateDeclined < dateSent))
			  ,('DeclinedState', not dateContested and not dateAccepted and dateDeclined and dateDeclined >= dateSent)
			  ,('AgreementState',(not dateContested and dateAccepted and dateAccepted >= dateSent) \
				    or (dateContested and dateContested > dateSent and dateAccepted < dateSent))
			  ,('CompletedState', (not dateContested and dateAccepted and dateAccepted < dateSent) \
				    or (dateContested and dateContested < dateSent and dateAccepted < dateContested))
			  ,('InvalidState', dateContested and dateAccepted and dateAccepted > dateSent)]
		
		# like find-first
		return [s[0] for s in states if s[1]][0]

	@classmethod
	def testCurrentState(clz):
		from datetime import datetime
		agreementInstance = OrderedDict([('dateCreated', datetime(2011, 8, 1)),
						 ('dateSent', None),
						 ('dateAccepted', None),
						 ('dateModified', None),
						 ('dateDeclined', None),
						 ('dateVerified', None), 
						 ('dateContested', None)])
		assert currentState(agreementInstance)=='DraftState'
		for day, (col, state) in enumerate([('dateSent', 'EstimateState')
						    ,('dateDeclined', 'DeclinedState')
						    ,('dateSent', 'EstimateState')
						    ,('dateAccepted', 'AgreementState')
						    ,('dateSent', 'CompletedState')
						    ,('dateContested', 'AgreementState')
						    ,('dateSent', 'CompletedState')
						    ,('dateVerified' ,'PaidState')]):
			agreementInstance[col]=datetime(2011, 8, day+1)
			assert currentState(agreementInstance)==state


class DraftState(AgreementStates):
	
	def __init__(self, agreementInstance):
		super(DraftState, self).__init__(agreementInstance)
		self.setButtons(["edit", "send"], 'vendor')
		self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=send"), "send", 'vendor')
		self.addActions(self.addFormActions("/agreement/%d.json" % self.agreementInstance.id, "GET", "edit=true"), "edit", 'vendor')
		print self._buttons


class EstimateState(AgreementStates):

	def __init__(self, agreementInstance):
		super(EstimateState, self).__init__(agreementInstance)
		self.setButtons(["edit"], vendorOrClient='vendor')
		self.setButtons(["accept", "decline"], vendorOrClient='client')
		self.addActions(self.addFormActions("/agreement/%d.json" % self.agreementInstance.id, "GET", "edit=true"), 'edit', 'vendor')
		self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=accept"), 'accept', 'client')
		self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=decline"), 'decline', 'client')

class DeclinedState(AgreementStates):

	def __init__(self, agreement):
		super(DeclinedState, self).__init__(agreementInstance)
		self.setButtons(["edit", "send"], vendorOrClient='vendor')
		self.addActions(self.addFormActions("/agreement/%d.json" % self.agreementInstance.id, "GET", "edit=true"), 'edit', 'client')
		self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=send"), 'send', 'client')

class AgreementState(AgreementStates):
	
	def __init__(self, agreement):
		super(AgreementState, self).__init__(agreementInstance)
		self.setButtons([mark_completed], vendorOrClient='vendor')
		self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=markComplete"), 'mark_completed', 'vendor')

class CompletedState(AgreementStates):
	
	def __init__(self, agreement):
		super(CompletedState, self).__init__(agreementInstance)
		self.setButtons([verify, dispute], vendorOrClient='client')
		self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=verify"), 'verify', 'client')
		self.addActions(self.addFormActions("/ageement/%d/status.json" % self.agreementInstance.id, "POST", "action=dispute"), 'dispute', 'client')
