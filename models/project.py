from controllers.orm import *

# -------------------------------------------------------------------
# Projects
# -------------------------------------------------------------------

class Project(MappedObj):
	
	def __init__(self):
		self.id = None
		self.userID = None
		self.clientID = None
		self.name = None
	
	@classmethod
	def tableName(clz):
		return "project"
	
	@classmethod
	def iteratorWithUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s" % clz.tableName(), userID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()