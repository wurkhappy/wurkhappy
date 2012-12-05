from controllers.orm import *
from controllers.amazonaws import *
# from controllers.base import Base16, Base58
from controllers.data import Data, Base58
from profile import Profile

from models.paymentmethod import PaymentMethod
from controllers.fmt import HTTPErrorBetter
import json
import uuid
import bcrypt
from hashlib import sha1

from boto.s3.key import Key
import logging

# For date-related queries, esp. w/ timezone support
from datetime import datetime
import pytz



# -------------------------------------------------------------------
# Users
# -------------------------------------------------------------------

class User(MappedObj):
	tableName = 'user'
	columns = {
		'id': None,
		'email': None,
		'confirmation': None,
		'fingerprint': None,
		'invitedBy': None,
		'inviteCode': None,
		# 'subscriberStatus': 0, # TODO: Delete field from schema
		'firstName': None,
		'lastName': None,
		'telephone': None,
		'password': None,
		'accessToken': None,
		'accessTokenSecret': None,
		'accessTokenExpiration': None,
		'profileOrigURL': None,
		'profileSmallURL': None,
		'profileLargeURL': None,
		'dateCreated': None,
		'dateInvited': None,
		'dateVerified': None,
		'dateLocked': None,
	}
	
	@classmethod
	def count(clz):
		with Database() as (conn, cursor):
			cursor.execute("SELECT COUNT(*) FROM {0}".format(clz.tableName))
			result = cursor.fetchone()
		
		return result['COUNT(*)']
	
	@classmethod
	def countRecentSignups(clz):
		tz = pytz.timezone("US/Eastern")
		midnight = tz.localize(
			datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None),
			is_dst=None
		)
		utc_dt = midnight.astimezone(pytz.utc)
      
		with Database() as (conn, cursor):
			cursor.execute("SELECT COUNT(*) FROM {0} WHERE dateCreated > %s".format(clz.tableName), midnight)
			result = cursor.fetchone()
		
		return result['COUNT(*)']
	
	@classmethod
	def retrieveByEmail(clz, email):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM %s WHERE email = %%s LIMIT 1" % clz.tableName, email.lower())
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
	
	@classmethod
	def retrieveByFingerprint(clz, fingerprint):
		with Database() as (conn, cursor):
			query = "SELECT * FROM {0} WHERE fingerprint = %s"
			cursor.execute(query.format(clz.tableName), fingerprint)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	@classmethod
	def retrieveByToken(clz, token):
		token = UserToken.retrieveByToken(token)
		return token and clz.retrieveByID(token['userID'])
	
	@classmethod
	def retrieveByAccessToken(clz, token):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM {0} WHERE accessToken = %s LIMIT 1".format(clz.tableName), token)
			result = cursor.fetchone()
		
		return clz.initWithDict(result)
		
	@classmethod
	def retrieveByUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM {0} WHERE id = %s LIMIT 1".format(clz.tableName), userID)
			result = cursor.fetchone()

		return clz.initWithDict(result)
	
	@classmethod
	def iteratorWithContactsForID(clz, userID):
		with Database() as (conn, cursor):
			query = """SELECT {0}.* FROM {0}
				LEFT JOIN agreement AS a ON user.id = a.clientID
				LEFT JOIN agreement AS b ON user.id = b.vendorID
				WHERE b.clientID = %s OR a.vendorID = %s
				GROUP BY user.id""".format(clz.tableName)
			
			cursor.execute(query, (userID, userID))
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def iteratorWithPage(clz, page):
		with Database() as (conn, cursor):
			query = "SELECT * FROM {0} ORDER BY id ASC LIMIT %s, %s".format(clz.tableName)
			cursor.execute(query, (page[0], page[1]))
			result = cursor.fetchone()
			
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	def setProfileImage(self, data, ext, headers=None):
		# TODO: Move this method to a more appropriate class. (Some sort of aux class or something?)
		
		digest = sha1(uuid.uuid4().bytes).digest()
		hashString = Data(digest).stringWithEncoding(Base58)
		
		name = '%s%s' % (hashString, ext)
		with AmazonS3() as (conn, bucket):
			k = Key(bucket)
			k.key = name
			k.set_contents_from_string(data, headers)
			k.make_public()
		
		self['profileOrigURL'] = 'https://media.wurkhappy.com.s3.amazonaws.com/{0}'.format(name)
		self.save()
	
	
	def getProfile(self):
		return Profile.retrieveByUserID(self['id'])
	
	def getFullName(self):
		"""
		Return the first and last name of the user, or if no values are set,
		the user's email address.
		"""
		return ' '.join([str(self['firstName'] or ''), str(self['lastName'] or '')]).strip() or self['email']
	
	def setPasswordHash(self, password):
		"Store the user's encrypted password"
		
		self['password'] = bcrypt.hashpw(str(password), bcrypt.gensalt())
	
	def passwordIsValid(self, password):
		if self['password'] is None:
			logging.warn(json.dumps({
				"domain": "model.consistency",
				"message": "This user is missing a valid 'password' record.",
				"userID": self['id']
			}))
			return False
		return self['password'] == bcrypt.hashpw(str(password), self['password'])
	
	def setConfirmationHash(self, confirmation):
		"Store the confirmation code's fingerprint and encrypted value"
		
		# The confirmation code is a password equivalent, so we must take care
		# to protect the plaintext from appearing in the database. However,
		# confirmation codes also must be indexed and searchable, so we need
		# to store a unique fingerprint.
		# 
		# We do this by storing an SHA-1 digest of the confirmation code that is
		# indexed, and a bcrypt encrypted ciphertext of the code for verification.
		
		self['fingerprint'] = sha1(confirmation).hexdigest()
		self['confirmation'] = bcrypt.hashpw(str(confirmation), bcrypt.gensalt())
	
	def confirmationIsValid(self, confirmation):
		"""
		Validate the user based on the supplied confirmation code. Similar to
		the User.passwordIsValid(password) method. A confirmation code is only
		valid if there is no password set for the user.
		"""
		cipherText = bcrypt.hashpw(str(confirmation), self['confirmation'])
		return self['password'] is None and self['confirmation'] == cipherText
	
	def getDefaultPaymentMethod(self):
		paymentPref = UserPrefs.retrieveByUserIDAndName(self['id'], 'preferredPaymentID')
		
		if paymentPref:
			paymentMethod = PaymentMethod.retrieveByID(paymentPref.value)
		else:
			paymentMethod = PaymentMethod.retrieveACHMethodWithUserID(self['id'])
			
			if not paymentMethod:
				paymentMethod = PaymentMethod.retrieveCCMethodWithUserID(self['id'])
		
		return paymentMethod
	
	def getCurrentState(self):
		"""
		Return the UserState subclass that represents the user's current state
		in the invitation and sign-up process.
		"""
		
		dateCreated = self['dateCreated']
		email = self['email']
		invitedBy = self['invitedBy']
		password = self['password']
		dateInvited = self['dateInvited']
		dateVerified = self['dateVerified']
		dateLocked = self['dateLocked']
		
		states = [
			(InvalidUserState, dateLocked),
			(ActiveUserState, password and dateVerified and email),
			(PendingUserState, dateInvited and email and dateCreated),
			(NewUserState, dateCreated and email and password),
			(InvitedUserState, dateCreated and email and invitedBy),
			(BetaUserState, dateCreated and email),
			(InvalidUserState, True)
		]
		
		# logging.info([s[0] for s in states if s[1]])
		state = [s[0] for s in states if s[1]][0]
		return state(self)
		
	def getPublicDict(self):
		return {
			'id': self['id'],
			'firstName': self['firstName'],
			'lastName': self['lastName'],
			'fullName': self.getFullName(),
			'email': self['email'],
			'telephone': self['telephone'],
			'profileURL': [
				self['profileSmallURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg',
				self['profileLargeURL'] or 'http://media.wurkhappy.com/images/profile1_s.jpg'
			],
			'dateCreated': self['dateCreated']
		}



# -------------------------------------------------------------------
# User Preferences
# -------------------------------------------------------------------

class UserPrefs(MappedObj):
	tableName = 'userPrefs'
	columns = {
		'id': None,
		'userID': None,
		'name': None,
		'value': None,
		'dateDeleted': None
	}
	
	@classmethod
	def iteratorWithUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM {0} WHERE userID = %s AND dateDeleted is NULL".format(clz.tableName), userID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def retrieveByUserIDAndName(clz, userID, name):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM {0} WHERE userID = %s AND name = %s AND dateDeleted is NULL".format(clz.tableName), (userID, name))
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	def getPublicDict(self):
		return {
			"name": self['name'],
			"value": self['value']
		}



# -------------------------------------------------------------------
# Dwolla Account Information
# -------------------------------------------------------------------

class UserDwolla(MappedObj):
	tableName = 'userDwolla'
	columns = {
		'id': None,
		'userID': None, # Unique key
		'dwollaID': None,
		'userName': None,
		'oauthToken': None,
		'status': None
	}
	
	@classmethod
	def retrieveByUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM {0} WHERE userID = %s".format(clz.tableName), userID)
			return clz.initWithDict(cursor.fetchone())
	
	@classmethod
	def retrieveByDwollaID(clz, dwollaID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM {0} WHERE dwollaID = %s".format(clz.tableName), dwollaID)
			return clz.initWithDict(cursor.fetchone())
	
	def getPublicDict(self):
		return { }



# -------------------------------------------------------------------
# User Tokens
# -------------------------------------------------------------------

class UserToken(MappedObj):
	# TODO: Make these expire after a few days.
	
	tableName = 'userToken'
	columns = {
		'id': None,
		'userID': None, # Multiple key
		'hash':  None,
		'fingerprint': None, # Unique key
		'expires': None
	}
	
	@classmethod
	def retrieveByToken(clz, token):
		fingerprint = sha1(token).hexdigest()
		with Database() as (conn, cursor):
			cursor.execute("SELECT * FROM {0} WHERE fingerprint = %s".format(clz.tableName), fingerprint)
			instance = clz.initWithDict(cursor.fetchone())
			if instance.tokenIsValid(token):
				return instance
			else:
				return None
	
	@classmethod
	def countWithUserID(clz, userID):
		with Database() as (conn, cursor):
			cursor.execute("SELECT COUNT(*) FROM {0} WHERE userID = %s".format(clz.tableName), userID)
			count = cursor.fetchone()
			return count['COUNT(*)']
	
	def tokenIsValid(self, token):
		return self['hash'] == bcrypt.hashpw(str(token), self['hash'])
	
	def setTokenHash(self, token):
		self['fingerprint'] = sha1(token).hexdigest()
		self['hash'] = bcrypt.hashpw(str(token), bcrypt.gensalt())



# -------------------------------------------------------------------
# State Transition Error (move to models.errors?)
# -------------------------------------------------------------------

class StateTransitionError(AssertionError):
	pass



# -------------------------------------------------------------------
# User State
# -------------------------------------------------------------------

class UserState(object):
	""" UserState """
	
	def __init__(self, user):
		assert type(user) == User
		self.user = user
	
	def performTransition(self, action, data):
		""" currentState : string, dict -> UserState """
		
		try:
			return self._prepareFields(action, data)
		except StateTransitionError as e:
			error = {
				"domain": "application.consistency",
				"display": (
					"There was a problem with your request. Our engineering "
					"team has been notified and will look into it."
				),
				"debug": "state transition error"
			}
			
			raise HTTPErrorBetter(409, 'state transition error ({0})'.format(e), json.dumps(error))
		
		return self.user.getCurrentState()



class BetaUserState(UserState):
	def __init__(self, agreementInstance):
		super(BetaUserState, self).__init__(agreementInstance)
	
	def __str__(self):
		return 'Requested beta access'
	
	def _prepareFields(self, action, data):
		if action is "send_verification":
			if not self.user['dateInvited']:
				self.user['dateInvited'] = datetime.now()
		else:
			raise StateTransitionError('unknown action for BetaUserState')



class InvitedUserState(UserState):
	def __init__(self, agreementInstance):
		super(InvitedUserState, self).__init__(agreementInstance)
	
	def __str__(self):
		return 'Invited by existing user and awaiting verification'
	
	def _prepareFields(self, action, data):
		if action is "send_verification":
			if not self.user['dateInvited']:
				self.user['dateInvited'] = datetime.now()
		else:
			raise StateTransitionError('unknown action for InvitedUserState')



class NewUserState(UserState):
	def __init__(self, agreementInstance):
		super(NewUserState, self).__init__(agreementInstance)
	
	def __str__(self):
		return 'Signed up on landing page and awaiting verification'
	
	def _prepareFields(self, action, data):
		if action is "send_verification":
			if not self.user['dateInvited']:
				self.user['dateInvited'] = datetime.now()
		else:
			raise StateTransitionError('unknown action for NewUserState')



class PendingUserState(UserState):
	def __init__(self, agreementInstance):
		super(PendingUserState, self).__init__(agreementInstance)
	
	def __str__(self):
		return 'Waiting for user to verify email address'
	
	def _prepareFields(self, action, data):
		if action is "confirm":
			if not self.user['password'] and 'password' not in data:
				raise StateTransitionError("missing required password field")
			else:
				self.user.setPasswordHash(data['password'])
			
			self.user['dateVerified'] = datetime.now()
		elif action is "send_verification":
			if not self.user['dateInvited']:
				self.user['dateInvited'] = datetime.now()
		else:
			logging.warn(self.user)
			logging.warn(action)
			raise StateTransitionError('unknown action for PendingUserState')



class ActiveUserState(UserState):
	def __init__(self, agreementInstance):
		super(ActiveUserState, self).__init__(agreementInstance)
	
	def __str__(self):
		return 'Active user'
	
	def _prepareFields(self, action, data):
		raise StateTransitionError('no actions allowed for ActiveUserState')



class InvalidUserState(UserState):
	def __init__(self, agreementInstance):
		super(InvalidUserState, self).__init__(agreementInstance)
	
	def __str__(self):
		return 'Locked account'
	
	def _prepareFields(self, action, data):
		raise StateTransitionError('no actions allowed for InvalidUserState')
