from tools.orm import *
from profile import Profile

# -------------------------------------------------------------------
# Agreements
# -------------------------------------------------------------------

class Agreement(MappedObj):
	
	def __init__(self):
		self.id = None
		self.vendorID = None
		self.clientID = None
		self.name = None
		self.amount = None
		self.dateCreated = None
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
			cursor.execute("SELECT SUM(amount) FROM %s WHERE vendorID = %%s" % clz.tableName(), vendorID)
			result = cursor.fetchone()
			return result['SUM(amount)']
	
	@classmethod
	def amountWithClientID(clz, clientID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT SUM(amount) FROM %s WHERE clientID = %%s" % clz.tableName(), clientID)
			result = cursor.fetchone()
			return result['SUM(amount)']
	
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
		return {
			"id": self.id,
			"vendorID": self.vendorID,
			"clientID": self.clientID,
			"name": self.name,
			"dateCreated": self.dateCreated.strftime("%Y-%m-%dT%H:%M:%SZ"),
			"dateAccepted": self.dateAccepted.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateAccepted else None,
			"dateModified": self.dateModified.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateModified else None,
			"dateDeclined": self.dateDeclined.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateDeclined else None,
			"dateVerified": self.dateVerified.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateVerified else None,
			"dateContested": self.dateContested.strftime("%Y-%m-%dT%H:%M:%SZ") if self.dateContested else None
		}


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
	

	