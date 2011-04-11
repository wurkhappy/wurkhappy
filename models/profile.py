from tools.orm import *

# -------------------------------------------------------------------
# Profiles
# -------------------------------------------------------------------

class Profile(MappedObj):
	
	def __init__(self):
		self.id = None
		self.userID = None
		self.bio = None
		self.blogURL = None
		self.portfolioURL = None
		self.name = None
	
	@classmethod
	def tableName(clz):
		return "profile"
	
	@classmethod
	def retrieveByUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s LIMIT 1" % clz.tableName(), userID)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
		
	@classmethod
	def retrieveByUrlStub(clz, stub):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE urlStub = %%s LIMIT 1" % clz.tableName(), stub)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)