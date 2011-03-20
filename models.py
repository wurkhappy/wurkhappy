# WurkHappy Data Models
# Version 0.1
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2011

from tools.orm import *

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
	


# -------------------------------------------------------------------
# Profiles
# -------------------------------------------------------------------

class Profile(MappedObj):
	
	def __init__(self):
		self.id = None
		self.userID = None
		self.bio = None
	
	@classmethod
	def tableName(clz):
		return "profile"
	
	@classmethod
	def retrieveByUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE userID = %%s LIMIT 1" % clz.tableName(), userID)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)

# -------------------------------------------------------------------
# Forgot Password
# -------------------------------------------------------------------

class ForgotPassword(MappedObj):
	
	def __init__(self):
		self.id = None
		self.userID = None
		self.code = None
		self.validUntil = None
		self.active = 0
	
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
	
