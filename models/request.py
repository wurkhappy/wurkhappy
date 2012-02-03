from collections import OrderedDict
from controllers.orm import Database, MappedObj

class Request(MappedObj):
	tableName = 'request'
	columns = {
		'id': None,
		'clientID': None,
		'vendorID': None,
		'dateCreated': None,
		'message': None
	}
	
	@classmethod
	def iteratorWithClientIDAndVendorID(clz, clientID, vendorID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE clientID = %%s AND vendorID = %%s"
			cursor.execute(query % clz.tableName, clientID, vendorID)
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	def publicDict(self):
		return OrderedDict([
			('id', self['id']),
			('clientID', self['clientID']),
			('vendorID', self['vendorID']),
			('dateCreated', self['dateCreated']),
			('message', self['message'])
		])