from __future__ import division
from controllers.orm import *
from collections import OrderedDict
from datetime import datetime
from controllers.fmt import HTTPErrorBetter
from models.errors import StateTransitionError

import json
import bcrypt
import hashlib
import logging



# -------------------------------------------------------------------
# Agreements
# -------------------------------------------------------------------

class Agreement(MappedObj):
	tableName = 'agreement'
	columns = {
		'id': None,
		'vendorID': None,
		'clientID': None,
		'name': None,
		'tokenFingerprint': None,
		'tokenHash': None,
		'dateCreated': None,
		'dateSent': None,
		'dateAccepted': None,
		'dateModified': None,
		'dateDeclined': None
	}
	
	@classmethod
	def countWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			query = "SELECT COUNT(*) FROM %s WHERE vendorID = %%s"
			cursor.execute(query % clz.tableName, vendorID)
			result = cursor.fetchone()
			return result['COUNT(*)']
	
	@classmethod
	def countWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			query = "SELECT COUNT(*) FROM %s WHERE clientID = %%s"
			cursor.execute(query % clz.tableName, clientID)
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
			cursor.execute(query % clz.tableName, vendorID)
			result = cursor.fetchone()
			return result['SUM(b.amount)']
	
	@classmethod
	def costStringWithClientID(clz, clientID):
		amount = clz.amountWithClientID(clientID)
		return "${:,f}".format(amount // 100) if amount else ""
	
	@classmethod
	def amountWithClientID(clz, clientID):
		# TODO: this needs to be checked. Not sure it's getting the right sum
		with Database() as (conn, cursor):
			query = """SELECT SUM(b.amount) FROM %s AS a
				LEFT JOIN agreementPhase AS b ON b.agreementID = a.id
				WHERE a.clientID = %%s AND a.dateAccepted IS NOT NULL
				AND b.dateVerified IS NULL
			"""
			cursor.execute(query % clz.tableName, clientID)
			result = cursor.fetchone()
			return result['SUM(b.amount)']
	
	@classmethod
	def retrieveByFingerprint(clz, fingerprint):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE tokenFingerprint = %%s"
			cursor.execute(query % clz.tableName, fingerprint)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	@classmethod
	def iteratorWithVendorID(clz, vendorID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE vendorID = %%s ORDER BY dateCreated DESC" % clz.tableName, vendorID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()		
	
	@classmethod
	def iteratorWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE clientID = %%s ORDER BY dateCreated DESC" % clz.tableName, clientID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()

	def getCostString(self, prefix='$', default=''):
		with Database() as (conn, cursor):
			cursor.execute("SELECT SUM(amount) FROM agreementPhase WHERE agreementID = %s", self['id'])
			amount = cursor.fetchone()['SUM(amount)']
			return "{0}{1:,.2f}".format(prefix, amount / 100) if amount else default
	
	def getCurrentPhase(self):
		with Database() as (conn, cursor):
			query = """SELECT * FROM agreementPhase WHERE agreementID = %s AND
				dateVerified IS NULL ORDER BY phaseNumber LIMIT 1"""
			cursor.execute(query, self['id'])
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
		
		dateSent =  self['dateSent']
		dateAccepted = self['dateAccepted']
		dateDeclined = self['dateDeclined']
		
		# Get the first agreement phase that has not been marked complete.
		phase = self.getCurrentPhase()
		phaseCount = AgreementPhase.countWithAgreementID(self['id'])
		
		dateCompleted = phase and phase['dateCompleted']
		dateVerified = phase and phase['dateVerified']
		dateContested = phase and phase['dateContested']
		
		# TODO: Unit test these against some example cases. Also make this fit the diagram above more closely.
		states = [
			# TODO: Final state as distinct from paid state. IMPORTANT
			# (Introduced phaseCount check to work around issue)
			# (FinalState, not phase),
			(PaidState, (dateVerified or not phase) and phaseCount > 0),
			# If phase is null, all phases are paid and
			# the agreement is in the final state.
			(ContestedState, dateAccepted and dateCompleted and dateContested and dateContested > dateCompleted),
			(CompletedState, dateAccepted and dateCompleted and (not dateContested or dateContested < dateCompleted)),
			(InProgressState, dateSent and dateAccepted),
			(EstimateState, dateSent and not dateAccepted and (not dateDeclined or (dateSent and dateDeclined < dateSent))),
			
			(DeclinedState, dateSent and dateDeclined and not dateAccepted),
			(DraftState, not dateSent),
			# The following will break shit, but we need to figure out how to do it:
			# (DraftState, not dateSent) or (dateDeclined and dateDeclined > dateSent)),
			(InvalidState, True)
		]

		subStateName = [s[0] for s in states if s[1]][0]
		return subStateName(self)
		
		
	
	def setTokenHash(self, token):
		self['tokenHash'] = bcrypt.hashpw(str(token), bcrypt.gensalt())
	
	def tokenIsValid(self, token):
		return self['tokenHash'] and self['tokenHash'] == bcrypt.hashpw(str(token), self['tokenHash'])
	
	def getPublicDict(self):
		return OrderedDict([
			('id', self['id']),
			('vendorID', self['vendorID']),
			('clientID', self['clientID']),
			('name', self['name']),
			('costString', self.getCostString()),
			('dateCreated', self['dateCreated']),
			('dateSent', self['dateSent']),
			('dateAccepted', self['dateAccepted']),
			('dateModified', self['dateModified']),
			('dateDeclined', self['dateDeclined']),
			# ('dateVerified', self.dateVerified),
			# ('dateContested', self.dateContested)
		])



# -------------------------------------------------------------------
# Agreements
# -------------------------------------------------------------------

class AgreementSummary(MappedObj):
	tableName = 'agreementSummary'
	columns = {
		'id': None,
		'agreementID': None,
		'summary': None,
		'comments': None
	}

	# @classmethod
	# def tableName(clz):
	# 	return "agreementSummary"
	
	@classmethod
	def retrieveByAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE agreementID = %%s" % clz.tableName, agreementID)
			result = cursor.fetchone()
			return clz.initWithDict(result)



# -----------------------------------------------------------------------------
# Agreement Phase
# -----------------------------------------------------------------------------

class AgreementPhase (MappedObj):
	tableName = 'agreementPhase'
	columns = {
		'id': None,
		'agreementID': None,
		'phaseNumber': None,
		'amount': None,
		'estDateCompleted': None,
		'dateCompleted': None,
		'dateVerified': None,
		'dateContested': None,
		'description': None,
		'comments': None
	}
	
	# @classmethod
	# def tableName(clz):
	# 	return "agreementPhase"
	
	@classmethod
	def iteratorWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE agreementID = %%s
				ORDER BY phaseNumber"""
			cursor.execute(query % clz.tableName, agreementID)
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def countWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			query = "SELECT COUNT(*) FROM {0} WHERE agreementID = %s"
			cursor.execute(query.format(clz.tableName), agreementID)
			result = cursor.fetchone()
			return result['COUNT(*)']
	
	@classmethod
	def retrieveByAgreementIDAndPhaseNumber(clz, agreementID, phaseNumber):
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE agreementID = %%s
				AND phaseNumber = %%s LIMIT 1"""
			cursor.execute(query % clz.tableName, (agreementID, phaseNumber))
			return clz.initWithDict(cursor.fetchone())
	
	def getCostString(self, prefix='$', default=''):
		return "{0}{1:,.2f}".format(prefix, self['amount'] / 100) if self['amount'] else default
	
	def getPublicDict(self):
		return OrderedDict([
			('phaseNumber', self['phaseNumber']),
			('amount', self['amount']),
			('costString', self.getCostString()),
			('estimatedCompletion', self['estDateCompleted']),
			('dateCompleted', self['dateCompleted']),
			('dateVerified', self['dateVerified']),
			('dateContested', self['dateContested']),
			('description', self['description']),
			('comments', self['comments'])
		])



# -------------------------------------------------------------------
# Agreement State
# -------------------------------------------------------------------

class AgreementState(object):
	""" AgreementState """
	
	# transitionNames = ["send", "save", "accept", "decline", "mark_complete", "dispute", "verify"]
	# fieldNames = ['dateSent', 'dateModified', 'dateAccepted', 'dateDeclined', 'dateCompleted', 'dateContested', 'dateVerified']
	# actionMap = dict(zip(transitionNames, fieldNames))
	
	inProgressPhaseNumber = None
	
	def __init__(self, agreementInstance):
		assert isinstance(agreementInstance, Agreement)
		self.agreement = agreementInstance
		# self.actions = {"vendor": {}, "client" : {}}
	
	# def addAction(self, role, actionName):
	# 	self.actions[role][actionName] = self.actionMap[actionName]
	
	def performTransition(self, role, action, unsavedRecords, **kwargs):
		""" currentState : string, dict -> AgreementState """
		
		self._prepareFields(role, action, unsavedRecords, **kwargs)
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
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			if self.agreement['clientID'] is None:
				raise StateTransitionError('missing required client for estimate', 'missingClient')
			
			if action == 'save':
				self.agreement['dateModified'] = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'send':
				# We require that an estimate have at least one phase in order to be sent.
				if (self.agreement.hasattr('phaseCount') and self.agreement.phaseCount == 0):
					raise StateTransitionError('missing agreement phases', 'missingPhases')
				
				if ('clientID' in self.agreement and self.agreement['clientID'] is None):
					raise StateTransitionError('missing agreement recipient', 'missingClient')

				self.agreement['dateSent'] = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError('unknown action for vendor in DraftState', 'unknownAction')
		else:
			raise StateTransitionError('incorrect role for DraftState', 'actionNotAllowed')

class EstimateState(AgreementState):
	def __init__(self, agreementInstance):
		super(EstimateState, self).__init__(agreementInstance)
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			raise StateTransitionError('3')
			if action == 'save':
				self.agreement['dateModified'] = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError('unknown action for vendor in EstimateState', 'unknownAction')
		elif role == 'client':
			if action == 'accept':
				self.agreement['dateAccepted'] = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'decline':
				self.agreement['dateDeclined'] = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError('unknown action for client in EstimateState', 'unknownAction')
		else:
			raise StateTransitionError('incorrect role for EstimatesState', 'actionNotAllowed')
	
class DeclinedState(AgreementState):
	def __init__(self, agreement):
		super(DeclinedState, self).__init__(agreement)
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			if action == 'save':
				self.agreement['dateModified'] = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'send':
				# We require that an estimate have at least one phase in order to be sent.
				if (self.agreement.hasattr('phaseCount') and self.agreement.phaseCount == 0):
					raise StateTransitionError('missing agreement phases', 'missingPhases')
				
				if ('clientID' in self.agreement and self.agreement['clientID'] is None):
					raise StateTransitionError('missing agreement recipient', 'missingClient')

				# If the agreement has been declined, reset previous comments
				# before re-sending the updated agreement. This also applies
				# to all of the agreement's phases.
				
				if self.agreement['dateDeclined']:
					summary = AgreementSummary.retrieveByAgreementID(self.agreement['id'])
					summary['comments'] = None
					unsavedRecords.append(summary)
				
				for phase in AgreementPhase.iteratorWithAgreementID(self.agreement['id']):
					if phase['comments']:
						phase['comments'] = None
						unsavedRecords.append(phase)
				
				self.agreement['dateModified'] = datetime.now()
				self.agreement['dateSent'] = datetime.now()
				unsavedRecords.append(self.agreement)
			else:
				raise StateTransitionError('unknown action for vendor in DeclinedState', 'unknownAction')
		else:
			raise StateTransitionError('incorrect role for DeclinedState', 'actionNotAllowed')
	
class InProgressState(AgreementState):
	def __init__(self, agreement):
		super(InProgressState, self).__init__(agreement)
	
	def _prepareFields(self, role, action, unsavedRecords, **kwargs):
		if role == 'vendor':
			if action == 'mark_complete':
				# The caller to InProgressState.performTransition() will pass
				# the phase as a keyword argument.
				phase = kwargs.get('phase', None)
				
				if phase: # logging.warn(phase)
					phase['dateCompleted'] = datetime.now()
					unsavedRecords.append(phase)
			else:
				raise StateTransitionError('unknown action for vendor in InProgressState', 'unknownAction')
		else:
			raise StateTransitionError('incorrect role for InProgressState', 'actionNotAllowed')

class CompletedState(AgreementState):
	def __init__(self, agreement):
		super(CompletedState, self).__init__(agreement)
	
	def _prepareFields(self, role, action, unsavedRecords, **kwargs):
		if role == 'client':
			if action == 'verify':
				phase = kwargs.get('phase', None)

				if phase:
					phase['dateVerified'] = datetime.now()
					unsavedRecords.append(phase)
			elif action == 'dispute':
				phase = kwargs.get('phase', None)

				if phase:
					phase['dateContested'] = datetime.now()
					unsavedRecords.append(phase)
			else:
				raise StateTransitionError('unknown action for client in CompletedState', 'unknownAction')
		else:
			raise StateTransitionError('incorrect role for CompletedState', 'actionNotAllowed')

class ContestedState(AgreementState):
	def __init__(self, agreement):
		super(ContestedState, self).__init__(agreement)
	
	def _prepareFields(self, role, action, unsavedRecords):
		if role == 'vendor':
			if action == 'save':
				self.agreement['dateModified'] = datetime.now()
				unsavedRecords.append(self.agreement)
			elif action == 'mark_complete':
				phase = self.agreement.getCurrentPhase()
				
				# Remove previous comments when re-sending
				phase['comments'] = None
				
				logging.warn(phase)
				phase['dateCompleted'] = datetime.now()
				unsavedRecords.append(phase)
			else:
				raise StateTransitionError('unknown action for vendor in ContestedState', 'unknownAction')
		else:
			raise StateTransitionError('incorrect role for ContestedState', 'actionNotAllowed')
	
class PaidState(AgreementState):
	def __init__(self, agreement):
		super(self.__class__, self).__init__(agreement)
	
	def _prepareFields(self, r, a, d):
		raise StateTransitionError('no actions allowed for PaidState', 'actionNotAllowed')
	
class InvalidState(AgreementState):
	def __init__(self, agreement):
		super(self.__class__, self).__init__(agreement)
	
	def _prepareFields(self, r, a, d):
		raise StateTransitionError('no actions allowed for InvalidState', 'actionNotAllowed')



