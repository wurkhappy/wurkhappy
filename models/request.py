from collections import OrderedDict
from controllers.orm import Database, MappedObj

class Request(MappedObj):
	table_name = "request"
	
	def __init__(self):
		self.id = None
		self.clientID = None
		self.vendorID = None
		self.dateCreated = None
		self.message = None
	
	@classmethod
	def tableName(clz):
		return clz.table_name
	
	@classmethod
	def iteratorWithClientIDAndVendorID(clz, clientID, vendorID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE clientID = %%s AND vendorID = %%s"
			cursor.execute(query % clz.table_name, clientID, vendorID)
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	def publicDict(self):
		return OrderedDict([
			('id', self.id),
			('clientID', self.clientID),
			('vendorID', self.vendorID),
			('dateCreated', self.dateCreated),
			('message', self.message)
		])