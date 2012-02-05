from controllers.orm import *

# -------------------------------------------------------------------
# Projects
# -------------------------------------------------------------------

class Project(MappedObj):
	tableName = 'project'
	columns = {
		'id': None,
		'userID': None,
		'clientID': None,
		'name': None
	}
	
	@classmethod
	def iteratorWithUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s" % clz.tableName, userID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()