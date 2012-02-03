from controllers.orm import *

# -------------------------------------------------------------------
# Profiles
# -------------------------------------------------------------------

class Profile(MappedObj):
	tableName = 'profile'
	columns = {
		'id': None,
		'userID': None,
		'bio': None,
		'blogURL': None,
		'portfolioURL': None,
		'name': None
	}
	
	@classmethod
	def retrieveByUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s LIMIT 1" % clz.tableName, userID)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
		
	@classmethod
	def retrieveByUrlStub(clz, stub):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE urlStub = %%s LIMIT 1" % clz.tableName, stub)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)