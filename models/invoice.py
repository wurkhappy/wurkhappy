from tools.orm import *

# -------------------------------------------------------------------
# Invoices
# -------------------------------------------------------------------

class Invoice(MappedObj):

	def __init__(self):
		self.id = None
		self.userID = None
		self.clientID = None
		self.projectID = None
		self.dateCreated = None
		self.dateSent = None
		self.datePaid = None

	@classmethod
	def tableName(clz):
		return "invoice"

	@classmethod
	def iteratorWithProjectID(clz, projectID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE projectID = %%s" % clz.tableName(), projectID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()