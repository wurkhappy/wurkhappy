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


