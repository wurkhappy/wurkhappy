from tools.orm import *
from tools.amazonaws import *
from tools.base import Base16, Base58
from profile import Profile

import uuid
import bcrypt
from hashlib import sha1

from boto.s3.key import Key
import logging



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
		self.subscriberStatus = None
		self.firstName = None
		self.lastName = None
		self.telephone = None
		self.password = None
		self.accessToken = None
		self.accessTokenSecret = None
		self.accessTokenExpiration = None
		self.profileOrigURL = None
		self.profileSmallURL = None
		self.profileLargeURL = None
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
	
	@classmethod
	def iteratorWithContactsForID(clz, userID):
		with Database() as (conn, cursor):
			query = """SELECT %s.* FROM %s 
				LEFT JOIN agreement AS a ON user.id = a.clientID
				LEFT JOIN agreement AS b ON user.id = b.vendorID 
				WHERE b.clientID = %%s OR a.vendorID = %%s 
				GROUP BY user.id""" % (clz.tableName(), clz.tableName())
			
			cursor.execute(query, (userID, userID))
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	def setProfileImage(self, data, ext, headers=None):
		#TODO: Move this method to a more appropriate class.
		hashString = Base58(Base16(sha1(uuid.uuid4().bytes).hexdigest())).string
		name = '%s%s' % (hashString, ext)
		with AmazonS3() as (conn, bucket):
			k = Key(bucket)
			k.key = name
			k.set_contents_from_string(data, headers)
			k.make_public()
		self.profileOrigURL = 'http://media.wurkhappy.com/%s' % name
		self.save()
	
	
	def getProfile(self):
		return Profile.retrieveByUserID(self.id)
	
	def getFullName(self):
		return self.firstName + " " + self.lastName
	
	def setPasswordHash(self, password):
		self.password = bcrypt.hashpw(str(password), bcrypt.gensalt())
	
	def passwordIsValid(self, password):
		return self.password == bcrypt.hashpw(str(password), self.password)
	
	def publicDict(self):
		return {
			"id": self.id,
			"email": self.email,
			"name": self.getFullName(),
			"dateCreated": self.dateCreated
		}



# -------------------------------------------------------------------
# User Preferences
# -------------------------------------------------------------------

class UserPrefs(MappedObj):

	def __init__(self):
		self.id = None
		self.userID = None
		self.name = None
		self.value = None
	
	@classmethod
	def tableName(clz):
		return "userPrefs"
	
	@classmethod
	def iteratorWithUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s" % clz.tableName(), userID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def retrieveByUserIDAndName(clz, userID, name):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s AND name = %%s" % clz.tableName(), (userID, name))
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	def publicDict(self):
		return {
			"name": self.name,
			"value": self.value
		}