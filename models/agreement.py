from tools.orm import *
from profile import Profile
from collections import OrderedDict
from datetime import datetime

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
		self.agreementInstance=agreementInstance
		# {'vendor' : [{"name" : "send", "text" : "Send Estimate", "db_action" : "SELECT ..."}} ...
		self.buttons = {"vendor": [], "client" : []}
		
		transitionNames = ["send","edit","accept","decline","mark_completed","dispute","verify"]
		fieldNames = ['dateSent', 'dateAccepted', 'dateDeclined', 'dateCompleted', 'dateContested', 'dateVerified']
		
		self._bmap = dict(zip(transitionNames, fieldNames))
		# self._jsmap = dict(zip(bnames, [{}
		# 				,{"action" : "/agreement/%d.json" % self.agreementInstance.id, "http" : "GET", 
		# add in js actions keywords?

	def getBmap(self, role, button):
		""" Returns the appropriate buttom mapping of the form button_name : column_name"""
		index = [i for (i, data) in enumerate(self._buttons[role]) if button in data][0]
		return self.buttons[role][index]

	def addButton(self, role, button_name):
		self.buttons[role].extend([{button_name : self._bmap[button_name]}])

	def doTransition(self, role, button):
		self.agreementInstance.__dict__[self.getBmap(role, button)[button]] = datetime.now()
		self.agreementInstance.save()
		return self.currentState(agreementInstance)

	@classmethod
	def currentState(clz, agreementInstance):
		""" currentState : Agreement -> AgreementState """
		
		dateVerified = agreementInstance.dateVerified
		dateSent =  agreementInstance.dateSent
		dateContested = agreementInstance.dateContested
		dateAccepted = agreementInstance.dateAccepted
		dateDeclined = agreementInstance.dateDeclined
		
		states = [('PaidState', dateVerified)
			  ,('DraftState', not dateSent)
			  ,('EstimateState', not dateContested and not dateAccepted and (not dateDeclined or dateDeclined < dateSent))
			  ,('DeclinedState', not dateContested and not dateAccepted and dateDeclined and dateDeclined >= dateSent)
			  # ,('AgreementState',(not dateContested and dateAccepted and dateAccepted >= dateSent) \
			  # 				    or (dateContested and dateContested > dateSent and dateAccepted < dateSent))
			  # ,('CompletedState', (not dateContested and dateAccepted and dateAccepted < dateSent) \
			  # 				    or (dateContested and dateContested < dateSent and dateAccepted < dateContested))
			  ,('AgreementState',(not dateContested and dateAccepted) or dateContested)
			  ,('CompletedState', (not dateContested and dateAccepted) or dateContested)
			  ,('InvalidState', dateContested and dateAccepted)]# and dateAccepted > dateSent)]
		
		# like find-first
		subStateName = [s[0] for s in states if s[1]][0]
		return globals()[subStateName](agreementInstance)

	@classmethod
	def testCurrentState(clz):
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
		self.addButton('vendor', "edit")
		self.addButton('vendor', "send")
		# self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=send"), "send", 'vendor')
		# self.addActions(self.addFormActions("/agreement/%d.json" % self.agreementInstance.id, "GET", "edit=true"), "edit", 'vendor')
		# print self.buttons



class EstimateState(AgreementStates):

	def __init__(self, agreementInstance):
		super(EstimateState, self).__init__(agreementInstance)
		self.addButton('vendor', "edit")
		self.addButton('client', "accept")
		self.addButton('client', "decline")
		# self.addActions(self.addFormActions(, "GET", "edit=true"), 'edit', 'vendor')
		# self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=accept"), 'accept', 'client')
		# self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=decline"), 'decline', 'client')

class DeclinedState(AgreementStates):

	def __init__(self, agreement):
		super(DeclinedState, self).__init__(agreement)
		self.addButton('vendor', "edit")
		self.addButton('vendor', "send")
		# self.addActions(self.addFormActions("/agreement/%d.json" % self.agreementInstance.id, "GET", "edit=true"), 'edit', 'client')
		# self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=send"), 'send', 'client')

class AgreementState(AgreementStates):
	
	def __init__(self, agreement):
		super(AgreementState, self).__init__(agreement)
		self.addButton('vendor', 'mark_completed')
		# self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=markComplete"), 'mark_completed', 'vendor')

class CompletedState(AgreementStates):
	
	def __init__(self, agreement):
		super(CompletedState, self).__init__(agreement)
		self.addButton('client', 'verify')
		self.addButton('client', 'dispute')
		# self.addActions(self.addFormActions("/agreement/%d/status.json" % self.agreementInstance.id, "POST", "action=verify"), 'verify', 'client')
		# self.addActions(self.addFormActions("/ageement/%d/status.json" % self.agreementInstance.id, "POST", "action=dispute"), 'dispute', 'client')

class PaidState(AgreementStates):
	def __inti__(self, agreement):
		super(self.__class__, self).__init__(agreement)
	