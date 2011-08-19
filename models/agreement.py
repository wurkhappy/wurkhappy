from tools.orm import *
from profile import Profile
from collections import OrderedDict
from datetime import datetime

import logging
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
		self.dateCompleted = None
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
	
	transitionNames = ["send","edit","accept","decline","mark_completed","dispute","verify"]
	fieldNames = ['dateSent', 'dateModified', 'dateAccepted', 'dateDeclined', 'dateCompleted', 'dateContested', 'dateVerified']
	
	def __init__(self, agreementInstance):
		assert type(agreementInstance) == Agreement
		self.agreementInstance=agreementInstance
		self.buttons = {"vendor": {}, "client" : {}}
		self._bmap = dict(zip(self.transitionNames, self.fieldNames))

	def addButton(self, role, button_name):
		self.buttons[role][button_name] = self._bmap[button_name]

	def doTransition(self, role, button):
		self.agreementInstance.__dict__[self.buttons[role][button]] = datetime.now()
		self.agreementInstance.save()
		return self.currentState(self.agreementInstance)

	@classmethod
	def currentState(clz, agreementInstance):
		""" currentState : Agreement -> AgreementState """
		
		dateVerified = agreementInstance.dateVerified
		dateSent =  agreementInstance.dateSent
		dateContested = agreementInstance.dateContested
		dateAccepted = agreementInstance.dateAccepted
		dateDeclined = agreementInstance.dateDeclined
		dateCompleted = agreementInstance.dateCompleted
		
		states = [('PaidState', dateVerified)
			  ,('CompletedState', (not dateContested and dateAccepted and dateCompleted))
			  ,('DraftState', not dateSent)
			  ,('EstimateState', not dateContested and not dateAccepted and (not dateDeclined or dateDeclined < dateSent))
			  ,('DeclinedState', not dateContested and not dateAccepted and dateDeclined and dateDeclined > dateSent)
			  ,('AgreementState', (not dateContested and dateAccepted and dateAccepted > dateSent) \
 				    or (dateContested and dateContested > dateSent and dateAccepted < dateSent))
			  ,('InvalidState', True)]
		
		# like find-first
		logging.info([s[0] for s in states if s[1]])
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

class EstimateState(AgreementStates):
	def __init__(self, agreementInstance):
		super(EstimateState, self).__init__(agreementInstance)
		self.addButton('vendor', "edit")
		self.addButton('client', "accept")
		self.addButton('client', "decline")

class DeclinedState(AgreementStates):
	def __init__(self, agreement):
		super(DeclinedState, self).__init__(agreement)
		self.addButton('vendor', "edit")
		self.addButton('vendor', "send")

class AgreementState(AgreementStates):
	def __init__(self, agreement):
		super(AgreementState, self).__init__(agreement)
		self.addButton('vendor', 'mark_completed')

class CompletedState(AgreementStates):
	def __init__(self, agreement):
		super(CompletedState, self).__init__(agreement)
		self.addButton('client', 'verify')
		self.addButton('client', 'dispute')

class PaidState(AgreementStates):
	def __init__(self, agreement):
		super(self.__class__, self).__init__(agreement)
	
	def doTransition(self, r, b):
		return self
	
class InvalidState(AgreementStates):
	def __init__(self, agreement):
		super(self.__class__, self).__init__(agreement)
	
	def doTransition(self, r, b):
		return self
