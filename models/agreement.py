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
			cursor.execute("SELECT SUM(a.amount) FROM %s AS a \
				LEFT JOIN agreementPhase AS b ON b.agreementID = a.id \
				WHERE a.vendorID = %%s AND a.dateAccepted IS NOT NULL \
				AND a.dateVerified IS NULL" % clz.tableName(), vendorID)
			result = cursor.fetchone()
			return result['SUM(a.amount)']
	
	@classmethod
	def amountWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT SUM(a.amount) FROM %s AS a \
				LEFT JOIN agreementPhase AS b ON b.agreementID = a.id \
				WHERE a.clientID = %%s AND a.dateAccepted IS NOT NULL \
				AND a.dateVerified IS NULL" % clz.tableName(), clientID)
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


