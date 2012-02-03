from controllers.orm import *

# -------------------------------------------------------------------
# Forgot Password
# -------------------------------------------------------------------

class ForgotPassword(MappedObj):
	columns = {
		'id': None,
		'userID': None,
		'code': None,
		'validUntil': None,
		'active': 0
	}
	
	@classmethod
	def tableName(clz):
		return "forgot_password"
	
	@classmethod
	def retrieveByUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s LIMIT 1" % clz.tableName(), userID)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
	
	@classmethod
	def retrieveByCode(clz, code):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE code = %%s LIMIT 1" % clz.tableName(), code)
			result = cursor.fetchone()

		return clz.initWithDict(result)