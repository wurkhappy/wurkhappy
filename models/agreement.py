from controllers.orm import *
from collections import OrderedDict
from datetime import datetime
from controllers.fmt import HTTPErrorBetter

import json
import bcrypt
import hashlib
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
		self.tokenFingerprint = None
		self.tokenHash = None
		self.dateCreated = None
		self.dateSent = None
		self.dateAccepted = None
		self.dateModified = None
		self.dateDeclined = None
		# self.dateCompleted = None
	
	@classmethod
	def tableName(clz):
		return "agreement"
	
	@classmethod
	def countWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			query = "SELECT COUNT(*) FROM %s WHERE vendorID = %%s"
			cursor.execute(query % clz.tableName(), vendorID)
			result = cursor.fetchone()
			return result['COUNT(*)']
	
	@classmethod
	def countWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			query = "SELECT COUNT(*) FROM %s WHERE clientID = %%s"
			cursor.execute(query % clz.tableName(), clientID)
			result = cursor.fetchone()
			return result['COUNT(*)']
	
	@classmethod
	def costStringWithVendorID(clz, vendorID):
		amount = clz.amountWithVendorID(vendorID)
		return "${:,f}".format(amount // 100) if amount else ""
	
	@classmethod
	def amountWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			query = """SELECT SUM(b.amount) FROM %s AS a
				LEFT JOIN agreementPhase AS b ON b.agreementID = a.id
				WHERE a.vendorID = %%s AND a.dateAccepted IS NOT NULL
				AND b.dateVerified IS NULL
			"""
			cursor.execute(query % clz.tableName(), vendorID)
			result = cursor.fetchone()
			return result['SUM(b.amount)']
	
	@classmethod
	def costStringWithClientID(clz, clientID):
		amount = clz.amountWithClientID(clientID)
		return "${:,f}".format(amount // 100) if amount else ""
	
	@classmethod
	def amountWithClientID(clz, clientID):
		# @todo: this needs to be checked. Not sure it's getting the right sum
		with Database() as (conn, cursor):
			query = """SELECT SUM(b.amount) FROM %s AS a
				LEFT JOIN agreementPhase AS b ON b.agreementID = a.id
				WHERE a.clientID = %%s AND a.dateAccepted IS NOT NULL
				AND b.dateVerified IS NULL
			"""
			cursor.execute(query % clz.tableName(), clientID)
			result = cursor.fetchone()
			return result['SUM(b.amount)']
	
	@classmethod
	def retrieveByFingerprint(clz, fingerprint):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE tokenFingerprint = %%s"
			cursor.execute(query % clz.tableName(), fingerprint)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	@classmethod
	def iteratorWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE vendorID = %%s ORDER BY dateCreated DESC" % clz.tableName(), vendorID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()		
	
	@classmethod
	def iteratorWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE clientID = %%s ORDER BY dateCreated DESC" % clz.tableName(), clientID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	def getCostString(self):
		with Database() as (conn, cursor):
			cursor.execute("SELECT SUM(amount) FROM agreementPhase WHERE agreementID = %s", self.id)
			amount = cursor.fetchone()['SUM(amount)']
			return "${:,.2f}".format(amount / 100) if amount else ""
	
	def getCurrentPhase(self):
		with Database() as (conn, cursor):
			query = """SELECT * FROM agreementPhase WHERE agreementID = %s AND
				dateVerified IS NULL ORDER BY phaseNumber LIMIT 1"""
			cursor.execute(query, self.id)
			result = cursor.fetchone()
			phase = AgreementPhase.initWithDict(result)
			return phase
	
	def getCurrentState(self):
		# The states are, in order:
		#   (D) DraftState
		#   (E) EstimateState
		#   (X) DeclinedState
		#   (A) AgreementState
		#   (M) MarkedState
		#   (C) ContestedState
		#   (V) VerifiedState
		#   (F) CompletedState
		# 
		# Double lined arrows ( ==> ) are state changes that occur on user
		# input. Single lined arrows ( --> ) are overlapping states (for
		# example, an agreement in the declined state also behaves as a
		# draft).
		# 
		# The "x" represents a hidden draft. The vendor has not yet sent it
		# to the client. The "1" and "2" markers represent the currently
		# active phase of the agreement.
		# 
		#     |  D  |  E  |  X  |  A  |  M  |  C  |  V  |  F  |
		#     |     |     |     |     |     |     |     |     |
		#     |  x ==> o ==> o ---.   |     |     |     |     |
		#     |     |     |     |  |  |     |     |     |     |
		#   ,---------------------/   |     |     |     |     |
		#  |  |     |     |     |     |     |     |     |     |
		#   \--> o ==> o ========> 1 ==> 1 ==> 1 ---.   |     |
		#     |     |     |     |     |     |     |  |  |     |
		#     |     |     |   ,---------------------/   |     |
		#     |     |     |  |  |     |     |     |     |     |
		#     |     |     |   \--> 1 ==> 1 ========> 1 ---.   |
		#     |     |     |     |     |     |     |     |  |  |
		#     |     |     |   ,---------------------------/   |
		#     |     |     |  |  |     |     |     |     |     |
		#     |     |     |   \--> 2 ==> 2 ========> 2 --> o  |
		#     |     |     |     |     |     |     |     |     |
		
		dateSent =  self.dateSent
		dateAccepted = self.dateAccepted
		dateDeclined = self.dateDeclined
		
		# Get the first agreement phase that has not been marked complete.
		phase = self.getCurrentPhase()
		
		dateCompleted = phase and phase.dateCompleted
		dateVerified = phase and phase.dateVerified
		dateContested = phase and phase.dateContested
		
		# @todo: Unit test these against some example cases. Also make this fit the diagram above more closely.
		states = [
			# (FinalState, not phase),
			(PaidState, dateVerified or not phase),
			# If phase is null, all phases are paid and
			# the agreement is in the final state.
			(ContestedState, dateAccepted and dateCompleted and dateContested and dateContested > dateCompleted),
			(CompletedState, dateAccepted and dateCompleted and (not dateContested or dateContested < dateCompleted)),
			(InProgressState, dateSent and dateAccepted),
			(EstimateState, dateSent and not dateContested and not dateAccepted and (not dateDeclined or (dateSent and dateDeclined < dateSent))),
			#                       |---------------------|  Do we need this?
			
			(DeclinedState, dateSent and dateDeclined and not dateAccepted),
			(DraftState, not dateSent), # The following will break shit, but we need to figure out how to do it: or (dateDeclined and dateDeclined > dateSent)),
			(InvalidState, True)
		]
		
		# like find-first
		# logging.info("(%d) %s: %s" % (self.id, self.name, [s[0] for s in states if s[1]]))
		subStateName = [s[0] for s in states if s[1]][0]
		return subStateName(self)
		
		
	
	def setTokenHash(self, token):
		self.tokenHash = bcrypt.hashpw(str(token), bcrypt.gensalt())
	
	def tokenIsValid(self, token):
		return self.tokenHash and self.tokenHash == bcrypt.hashpw(str(token), self.tokenHash)
	
	def publicDict(self):
		return OrderedDict([
			('id', self.id),
			('vendorID', self.vendorID),
			('clientID', self.clientID),
			('name', self.name),
			('costString', self.getCostString()),
			('dateCreated', self.dateCreated),
			('dateSent', self.dateSent),
			('dateAccepted', self.dateAccepted),
			('dateModified', self.dateModified),
			('dateDeclined', self.dateDeclined),
			# ('dateVerified', self.dateVerified),
			# ('dateContested', self.dateContested)
		])



# -------------------------------------------------------------------
# Agreements
# -------------------------------------------------------------------

class AgreementSummary(MappedObj):

	def __init__(self):
		self.id = None
		self.agreementID = None
		self.summary = None
		self.comments = None

	@classmethod
	def tableName(clz):
		return "agreementSummary"
	
	@classmethod
	def retrieveByAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE agreementID = %%s" % clz.tableName(), agreementID)
			result = cursor.fetchone()
			return clz.initWithDict(result)



# -----------------------------------------------------------------------------
# Agreement Phase
# -----------------------------------------------------------------------------

class AgreementPhase (MappedObj):
	
	def __init__(self):
		self.id = None
		self.agreementID = None
		self.phaseNumber = None
		self.amount = None
		self.estDateCompleted = None
		self.dateCompleted = None
		self.dateVerified = None
		self.dateContested = None
		self.description = None
		self.comments = None
	
	@classmethod
	def tableName(clz):
		return "agreementPhase"
	
	@classmethod
	def iteratorWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE agreementID = %%s
				ORDER BY phaseNumber"""
			cursor.execute(query % clz.tableName(), agreementID)
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def retrieveByAgreementIDAndPhaseNumber(clz, agreementID, phaseNumber):
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE agreementID = %%s
				AND phaseNumber = %%s LIMIT 1"""
			cursor.execute(query % clz.tableName(), (agreementID, phaseNumber))
			return clz.initWithDict(cursor.fetchone())
	
	def getCostString(self):
		return "${:,.2f}".format(self.amount / 100) if self.amount else ""
	
	def publicDict(self):
		return OrderedDict([
			('phaseNumber', self.phaseNumber),
			('amount', self.amount),
			('costString', self.getCostString()),
			('estimatedCompletion', self.estDateCompleted),
			('dateCompleted', self.dateCompleted),
			('dateVerified', self.dateVerified),
			('dateContested', self.dateContested),
			('description', self.description),
			('comments', self.comments)
		])



class StateTransitionError(Exception):
	pass

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
# InProgressState -> (dateAccepted > dateSent and dateContested null) or (dateContested > dateSent > dateAccepted)
#  vendor sees agreement, mark-completed buttons; mark-completed updates dateSent
#  client sees agreement
# CompletedState -> (dateSent > dateAccepted and dateContested null) or (dateSent > dateContested > dateAccepted)
#  vendor sees agreement
#  client sees agreement, dispute and verify buttons; dispute updates dateContested; verify updates dateVerified
# PaidState -> dateVerified is not null 
#  what to show?
# Do we store elsewhere a history of edits?
# -------------------------------------------------------------------

class AgreementState(object):
	""" AgreementState """
	
	transitionNames = ["send", "save", "accept", "decline", "mark_complete", "dispute", "verify"]
	fieldNames = ['dateSent', 'dateModified', 'dateAccepted', 'dateDeclined', 'dateCompleted', 'dateContested', 'dateVerified']
	actionMap = dict(zip(transitionNames, fieldNames))
	
	inProgressPhaseNumber = None
	
	def __init__(self, agreementInstance):#, phaseList):
		assert isinstance(agreementInstance, Agreement)
		self.agreement = agreementInstance
		self.actions = {"vendor": {}, "client" : {}}
	
	def addAction(self, role, actionName):
		self.actions[role][actionName] = self.actionMap[actionName]
	
	def doTransition(self, role, action):
		if role in self.actions and action in self.actions[role]:
			self.agreement.__dict__[self.actions[role][action]] = datetime.now()
			self.agreement.save()
		else:
			fmat = 'Invalid transition for agreement %d (role: %s, action: %s)'
			logging.error(fmat % (self.agreementInstance.id, role, action))
		
		return self.agreement.getCurrentState()
	
	def performTransition(self, role, action, unsavedRecords):
		""" currentState : string, dict -> AgreementState """
		
		try:
			return self._prepareFields(role, action, unsavedRecords)
		except StateTransitionError as e:
			# @todo: We need to separate this from model code. UGHHHH
			error = {
				"domain": "application.consistency",
				"display": (
					"There was a problem with your request. Our engineering "
					"team has been notified and will look into it."
				),
				"debug": "state transition error"
			}
			
			raise HTTPErrorBetter(409, 'state transition error', json.dumps(error))
		
		return self.agreement.getCurrentState()
	
	@classmethod
	def testCurrentState(clz):
		agreementInstance = OrderedDict([
			('dateCreated', datetime(2011, 8, 1)),
			('dateSent', None),
			('dateAccepted', None),
			('dateModified', None),
			('dateDeclined', None),
			('dateVerified', None), 
			('dateContested', None)
		])
		assert currentState(agreementInstance) == 'DraftState'
		
		stateList = [
			('dateSent', 'EstimateState'),
			('dateDeclined', 'DeclinedState'),
			('dateSent', 'EstimateState'),
			('dateAccepted', 'InProgressState'),
			('dateSent', 'CompletedState'),
			('dateContested', 'InProgressState'),
			('dateSent', 'CompletedState'),
			('dateVerified' ,'PaidState'),
		]
		
		for day, (col, state) in enumerate(stateList, 1):
			agreementInstance[col] = datetime(2011, 8, day)
			assert currentState(agreementInstance) == state

class DraftState(AgreementState):
	def __init__(self, agreementInstance):
		super(DraftState, self).__init__(agreementInstance)
		self.addAction('vendor', "save")
		self.addAction('vendor', "send")
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			if action == 'save':
				self.agreement.dateModified = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'send':
				self.agreement.dateSent = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError()
		else:
			raise StateTransitionError()

class EstimateState(AgreementState):
	def __init__(self, agreementInstance):
		super(EstimateState, self).__init__(agreementInstance)
		self.addAction('vendor', "save")
		self.addAction('client', "accept")
		self.addAction('client', "decline")
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			raise StateTransitionError()
			if action == 'save':
				self.agreement.dateModified = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError()
		elif role == 'client':
			if action == 'accept':
				self.agreement.dateAccepted = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'decline':
				self.agreement.dateDeclined = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError()
		else:
			raise StateTransitionError()
	
class DeclinedState(AgreementState):
	def __init__(self, agreement):
		super(DeclinedState, self).__init__(agreement)
		self.addAction('vendor', "save")
		self.addAction('vendor', "send")
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			if action == 'save':
				self.agreement.dateModified = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'send':
				# If the agreement has been declined, reset previous comments
				# before re-sending the updated agreement. This also applies
				# to all of the agreement's phases.
				
				if self.agreement.dateDeclined:
					summary = AgreementSummary.retrieveByAgreementID(self.agreement.id)
					summary.comments = None
					unsavedRecords.append(summary)
					#self.agreement.comments = None
				
				for phase in AgreementPhase.iteratorWithAgreementID(self.agreement.id):
					if phase.comments:
						phase.comments = None
						unsavedRecords.append(phase)
				
				self.agreement.dateModified = datetime.now()
				self.agreement.dateSent = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError()
		else:
			raise StateTransitionError()
	
class InProgressState(AgreementState):
	def __init__(self, agreement):
		super(InProgressState, self).__init__(agreement)
		self.addAction('vendor', 'mark_complete')
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			if action == 'mark_complete':
				# The caller to InProgressState.performTransition() will pass
				# the phase number as a value in the data dictionary.
				# phase = (p for p in self.phaseList if p.phaseNumber == data['phaseNumber'])[0]
				phase = self.agreement.getCurrentPhase()
				logging.warn(phase)
				phase.dateCompleted = datetime.now()
				unsavedRecords.append(phase)
			else:
				raise StateTransitionError()
		else:
			raise StateTransitionError()

class CompletedState(AgreementState):
	def __init__(self, agreement):
		super(CompletedState, self).__init__(agreement)
		self.addAction('client', 'verify')
		self.addAction('client', 'dispute')
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'client':
			if action == 'verify':
				# phase = (p for p in self.phaseList if p.phaseNumber == data['phaseNumber'])[0]
				phase = self.agreement.getCurrentPhase()
				phase.dateVerified = datetime.now()
				unsavedRecords.append(phase)
			elif action == 'dispute':
				# phase = (p for p in self.phaseList if p.phaseNumber == data['phaseNumber'])[0]
				phase = self.agreement.getCurrentPhase()
				phase.dateContested = datetime.now()
				unsavedRecords.append(phase)
			else:
				raise StateTransitionError()
		else:
			raise StateTransitionError()

class ContestedState(AgreementState):
	def __init__(self, agreement):
		super(ContestedState, self).__init__(agreement)
		self.addAction('vendor', 'save')
		self.addAction('vendor', 'send')
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			if action == 'save':
				self.agreement.dateModified = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'mark_complete':
				phase = self.agreement.getCurrentPhase()
				
				# Remove previous comments when re-sending
				phase.comments = None
				
				logging.warn(phase)
				phase.dateCompleted = datetime.now()
				unsavedRecords.append(phase)
			else:
				raise StateTransitionError()
		else:
			raise StateTransitionError()
	
class PaidState(AgreementState):
	def __init__(self, agreement):
		super(self.__class__, self).__init__(agreement)
	
	def doTransition(self, r, a):
		return self
	
	def _prepareFields(self, r, a, d):
		pass
	
class InvalidState(AgreementState):
	def __init__(self, agreement):
		super(self.__class__, self).__init__(agreement)
	
	def doTransition(self, r, a):
		return self
	
	def _prepareFields(self, r, a, d):
		pass
