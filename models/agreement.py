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
		self.dateCreated = None
	
	@classmethod
	def tableName(clz):
		return "agreement"
	
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
		
	def getTransactionIterator(self):
		return AgreementTxn.iteratorWithAgreementID(self.id)
	
	def getTextIterator(self):
		return AgreementTxt.iteratorWithAgreementID(self.id)
	


# -------------------------------------------------------------------
# Agreement Transactions
# -------------------------------------------------------------------

class AgreementTxn (MappedObj):
	
	def __init__(self):
		self.id = None
		self.agreementID = None
		self.userID = None
		self.status = None
		self.dateModified = None
	
	@classmethod
	def tableName(clz):
		return "agreementTxn"
	
	@classmethod
	def iteratorWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE agreementID = %%s" % clz.tableName(), agreementID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	


# -------------------------------------------------------------------
# Agreement Text
# -------------------------------------------------------------------

class AgreementTxt (MappedObj):
	
	def __init__(self):
		self.id = None
		self.agreementID = None
		self.agreement = None
		self.refund = None
		self.dateModified = None
	
	@classmethod
	def tableName(clz):
		return "agreementTxt"
	
	@classmethod
	def iteratorWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE agreementID = %%s" % clz.tableName(), agreementID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
