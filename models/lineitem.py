from tools.orm import *

# -------------------------------------------------------------------
# Line Items
# -------------------------------------------------------------------

class LineItem(MappedObj):

	def __init__(self):
		self.id = None
		self.invoiceID = None
		self.name = None
		self.description = None
		self.price = None
		self.quantity = None
	
	def getPublicDictionary(self):
		return {
			"id": self.id,
			"invoiceID": self.invoiceID,
			"name": self.name,
			"description": self.description,
			"price": self.price,
			"quantity": self.quantity
		}
	
	@classmethod
	def tableName(clz):
		return "lineItem"

	@classmethod
	def iteratorWithInvoiceID(clz, projectID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE invoiceID = %%s LIMIT 1" % clz.tableName(), projectID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()


