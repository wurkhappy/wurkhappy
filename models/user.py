from tools.orm import *
from profile import Profile

# -------------------------------------------------------------------
# Users
# -------------------------------------------------------------------

class User(MappedObj):
	
	def __init__(self):
		self.id = None
		self.email = None
		self.confirmationCode = None
		self.confirmationHash = None
		self.confirmed = None
		self.firstName = None
		self.lastName = None
		self.password = None
		self.accessToken = None
		self.accessTokenSecret = None
		self.accessTokenExpiration = None
		self.dateCreated = None
	
	@classmethod
	def tableName(clz):
		return "user"
	
	@classmethod
	def retrieveByEmail(clz, email):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE email = %%s LIMIT 1" % clz.tableName(), email)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
	
	@classmethod
	def retrieveByAccessToken(clz, token):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE accessToken = %%s LIMIT 1" % clz.tableName(), token)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
		
	@classmethod
	def retrieveByUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE id = %%s LIMIT 1" % clz.tableName(), userID)
			result = cursor.fetchone()

		return clz.initWithDict(result)
		
	def getProfile(self):
		return Profile.retrieveByUserID(self.id)
	
	def getFullName(self):
		return self.firstName + " " + self.lastName
