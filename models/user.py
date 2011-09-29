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
		self.invitedBy = None
		self.confirmed = None # @todo: Delete for next deploy
		self.subscriberStatus = 0 # @todo: Delete for next deploy
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
		self.dateVerified = None
	
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
		return " ".join([str(self.firstName or ""), str(self.lastName or "")]).strip()
	
	def setPasswordHash(self, password):
		self.password = bcrypt.hashpw(str(password), bcrypt.gensalt())
	
	def passwordIsValid(self, password):
		return self.password == bcrypt.hashpw(str(password), self.password)
	
	def publicDict(self):
		return {
			'id': self.id,
			'fullName': self.getFullName(),
			'email': self.email,
			'telephone': self.telephone,
			'profileURL': [
				self.profileSmallURL or '#',
				self.profileLargeURL or '#'
			],
			'dateCreated': self.dateCreated
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



class StateTransitionError(Exception):
	pass

# -------------------------------------------------------------------
# User State
# -------------------------------------------------------------------

class UserState(object):
	""" UserState """
	
	def __init__(self, user):
		assert type(user) == User
		self.user = user
	
	def doTransition(self, action, data):
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
			
			raise HTTPErrorBetter(409, 'state transition error', JSON.dumps(error))
		
		return UserState.currentState(self.user)
	
	@classmethod
	def currentState(clz, user):
		""" currentState : User -> UserState """
		
		dateCreated = user.dateCreated
		email = user.email
		invitedBy = user.invitedBy
		confirmationCode = user.confirmationCode
		confirmationHash = user.confirmationHash
		password = user.password
		dateVerified = user.dateVerified
		
		states = [
			(ActiveUserState, password and dateVerified and confirmationCode and confirmationHash and email),
			(PendingUserState, confirmationCode and confirmationHash and email and dateCreated),
			(NewUserState, dateCreated and email and password),
			(InvitedUserState, dateCreated and email and invitedBy),
			(BetaUserState, dateCreated and email),
			(InvalidUserState, True)
		]
		
		# like find-first
		logging.info([s[0] for s in states if s[1]])
		state = [s[0] for s in states if s[1]][0]
		return state(user)

	# @classmethod
	# def testCurrentState(clz):
	# 	agreementInstance = OrderedDict([('dateCreated', datetime(2011, 8, 1)),
	# 					 ('dateSent', None),
	# 					 ('dateAccepted', None),
	# 					 ('dateModified', None),
	# 					 ('dateDeclined', None),
	# 					 ('dateVerified', None), 
	# 					 ('dateContested', None)])
	# 	assert currentState(agreementInstance)=='DraftState'
	# 	for day, (col, state) in enumerate([('dateSent', 'EstimateState')
	# 					    ,('dateDeclined', 'DeclinedState')
	# 					    ,('dateSent', 'EstimateState')
	# 					    ,('dateAccepted', 'InProgressState')
	# 					    ,('dateSent', 'CompletedState')
	# 					    ,('dateContested', 'InProgressState')
	# 					    ,('dateSent', 'CompletedState')
	# 					    ,('dateVerified' ,'PaidState')]):
	# 		agreementInstance[col]=datetime(2011, 8, day+1)
	# 		assert currentState(agreementInstance)==state

class BetaUserState(UserState):
	def __init__(self, agreementInstance):
		super(DraftState, self).__init__(agreementInstance)
	
	def _prepareFields(self, action, data):
		if action is "send_verification":
			if 'confirmationCode' not in data or 'confirmationHash' not in data:
				raise StateTransitionError("missing required fields")
			
			self.user.confirmationCode = data['confirmationCode']
			self.user.confirmationHash = data['confirmationHash']
		else:
			raise StateTransitionError()

class InvitedUserState(UserState):
	def __init__(self, agreementInstance):
		super(DraftState, self).__init__(agreementInstance)
	
	def _prepareFields(self, action, data):
		if action is "send_verification":
			if 'confirmationCode' not in data or 'confirmationHash' not in data:
				raise StateTransitionError("missing required fields")
			
			self.user.confirmationCode = data['confirmationCode']
			self.user.confirmationHash = data['confirmationHash']
		else:
			raise StateTransitionError()

class NewUserState(UserState):
	def __init__(self, agreementInstance):
		super(DraftState, self).__init__(agreementInstance)
	
	def _prepareFields(self, action, data):
		if action is "send_verification":
			if 'confirmationCode' not in data or 'confirmationHash' not in data:
				raise StateTransitionError("missing required fields")
			
			self.user.confirmationCode = data['confirmationCode']
			self.user.confirmationHash = data['confirmationHash']
		else:
			raise StateTransitionError()

class PendingUserState(UserState):
	def __init__(self, agreementInstance):
		super(DraftState, self).__init__(agreementInstance)
	
	def _prepareFields(self, action, data):
		if action is "confirm":
			if not self.user.password and 'password' not in data:
				raise StateTransitionError("missing required password field")
			else:
				self.user.setPasswordHash(data['password'])
			
			self.user.dateVerified = datetime.now()
		else:
			raise StateTransitionError()

class ActiveUserState(UserState):
	def __init__(self, agreementInstance):
		super(DraftState, self).__init__(agreementInstance)
	
	def _prepareFields(self, action, data):
		raise StateTransitionError()
