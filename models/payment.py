from tools import orm
from collections import OrderedDict


# -------------------------------------------------------------------
# Payment
# -------------------------------------------------------------------

class Payment(MappedObject):
	def __init__(self):
		self.id = None
		self.fromClientID = None
		self.toVendorID = None
		self.agreementPhaseID = None
		self.amount = None
		self.dateInitiated = None
		self.dateDeclined = None
		self.dateAccepted = None
	
	@classmethod
	def tableName(clz):
		return 'payment'
	
	@classmethod
	def iteratorWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			query = """SELECT p.* FROM %s AS p
				LEFT JOIN agreementPhase AS b ON p.agreementPhaseID = b.id
				LEFT JOIN agreement AS a ON b.agreementID = a.id
				WHERE b.agreementID = %%s ORDER BY p."""
			cursor.execute(query % clz.tableName(), agreementID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@staticmethod
	def foo():
		pass
		
