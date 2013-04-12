from controllers.orm import *
from collections import OrderedDict



# -------------------------------------------------------------------
# Payment Methods
# -------------------------------------------------------------------
# A payment method is record of stored payment info. Eventually we'll
# want to have much more granular contol over what's going on here.

class UserPayment(MappedObj):
	tableName = 'userPayment'
	columns = {
		'id': None,
		'userID': None,
		'pmID': None,
		'pmTable': None,
		'isDefault': None,
		'dateDeleted': None
	}

	@classmethod
	def retrieveByPMIDAndPMTable(clz, pmID, pmTable):
		'''
		Retrieve the linking table record for a specified pmID and pmTable.
		'''

		query = 'SELECT * FROM {0} WHERE pmID = %s AND pmTable = %s'

		with Database() as (conn, cursor):
			cursor.execute(query.format(clz.tableName), (pmID, pmTable))
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	@classmethod
	def retrieveDefaultByUserID(clz, userID):
		'''
		Retrieve the linking table record for the default payment method
		for a given user ID.
		'''

		query = 'SELECT * FROM {0} WHERE userID = %s AND isDefault IS NOT NULL'

		with Database() as (conn, cursor):
			cursor.execute(query.format(clz.tableName), userID)
			result = cursor.fetchone()
			return clz.initWithDict(result)



class PaymentBase(MappedObj):
	'''
	Base class for payment method types
	'''
	
	@classmethod
	def retrieveByUserID(clz, userID):
		'''
		Retrieves only the payment method for a specified user ID where the 
		payment method type matches the PaymentBase subclass the method was
		called on.
		'''

		if clz is PaymentBase:
			raise NotImplementedError('you must call retrieveByUserID on a PaymentBase subclass')

		query = '''SELECT pm.* FROM userPayment up, {0} pm WHERE pm.id = up.pmID
			AND up.userID = %s AND up.dateDeleted IS NULL AND up.pmTable = "{0}"'''

		with Database() as (conn, cursor):
			cursor.execute(query.format(clz.tableName), userID)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	@classmethod
	def retrieveAllByUserID(clz, userID):
		'''
		Retrieves all payment method instances associated with the specified
		user ID. Searches for subclasses of PaymentBase and calls _retrieveByUserID
		on each subclass and returns a flattened list of payment methods found.
		'''
		
		query = '''SELECT pm.* FROM userPayment up, {0} pm WHERE pm.id = up.pmID
			AND up.pmTable = "{0}" AND up.dateDeleted IS NULL AND up.userID = %s'''
		
		with Database() as (conn, cursor):
			for c in clz.__subclasses__():
				cursor.execute(query.format(c.tableName), userID)
				result = cursor.fetchone()
				while result:
					yield c.initWithDict(result)
					result = cursor.fetchone()

		# IYI, a detail from the previous implementation of this method:
		# 
		# Let's say you have a list of lists:
		# 
		#     > x = [[1, 2], [3, 4], [5, 6, 7]]
		#
		# If you want to flatten the list, you could use itertools:
		# 
		#     > list(itertools.chain(*x))
		#     [1, 2, 3, 4, 5, 6, 7]
		# 
		# But did you know you can nest generators in list comprehensions?
		#
		#     > [item for sublist in x for item in sublist]
		#     [1, 2, 3, 4, 5, 6, 7]
		# 
		# Which can be thought of as a parallel construction of the following:
		# 
		#     > lst = []
		#     > for sublist in x:
		#     -     for item in sublist:
		#     -         lst.append(item)
		#     > lst
		#     [1, 2, 3, 4, 5, 6, 7]
		# 
		# I appologize for the baffling return statement below, but if it helps, you may
		# think of it as shown here:
		# 
		#     lst = []
		#     for c in clz.__subclasses__():
		#          for i in c._retrieveByUserID(userID))
		#              lst.append(i)
		#     return lst
	
	@classmethod
	def retrieveDefaultByUserID(clz, userID):
		'''
		Retrieves the payment method associated with the specified user ID
		that is marked as default, or None if none exists.
		'''

		query = '''SELECT pm.* FROM userPayment up JOIN {0} pm ON pm.id = up.pmID
			WHERE up.pmTable = "{0}" AND up.userID = %s AND up.dateDeleted IS NULL
			AND up.isDefault IS NOT NULL'''
		
		# We restrict the query further by requiring a default flag in the
		# userPayment record. We still iterate over all subclasses, since
		# we don't know which query will produce results. However, since we
		# enforce a unique index on the userID, default combination, we are
		# assured that there will only ever be one record.

		with Database() as (conn, cursor):
			for c in clz.__subclasses__():
				cursor.execute(query.format(c.tableName), userID)
				result = cursor.fetchone()
				while result:
					return c.initWithDict(result)
		return None

	def getPublicDict(self):
		raise NotImplementedError('Subclasses of PaymentBase must override getPublicDict')
	
	def canReceivePayment(self):
		raise NotImplementedError('Subclasses of PaymentBase must override canReceivePayment')

	def canSendPayment(self):
		raise NotImplementedError('Subclasses of PaymentBase must override canSendPayment')



class OOBPaymentMethod(PaymentBase):
	'''
	Out-of-band payments plug into the general payment architecture, but all
	handling of funds transfer is up to the involved parties. We require a
	postal address for this payment method because we assume that payment by
	check is the most common use case.
	'''

	tableName = 'oobPaymentMethod'
	columns = {
		'id': None,
		'address1': None,
		'address2': None,
		'city': None,
		'state': None,
		'postCode': None
	}
	
	def getPublicDict(self):
		return OrderedDict([
			('id', self['id']),
			('type', self.tableName),
			('address1', self['address1']),
			('address2', self['address2']),
			('city', self['city']),
			('state', self['state']),
			('postCode', self['postCode'])
		])
	
	def addressIsValid(self):
		return (
			self['address1'] and
			self['city'] and
			self['state'] and
			self['postCode']
		)
	
	def canReceivePayment(self):
		return self.addressIsValid()
	
	def canSendPayment(self):
		return self.addressIsValid()

	def displayString(self):
		return '''{address1}<br />
		{address2}<br />
		{city}, {state} {postCode}
		'''.format(self.getPublicDict())



class AmazonPaymentMethod(PaymentBase):
	tableName = 'amazonPaymentMethod'
	columns = {
		'id': None,
		'tokenID': None,
		'tokenSecretID': None,
		'recipientEmail': None,
		'variableMarketplaceFee': None,
		'verificationComplete': None
	}
	
	def getPublicDict(self):
		return OrderedDict([
			('id', self['id']),
			('type', self.tableName),
			('tokenID', self['tokenID']),
			('recipientEmail', self['recipientEmail']),
			('verificationComplete', self['verificationComplete'])
		])
	
	def canReceivePayment(self):
		return self['verificationComplete'] == True

	def canSendPayment(self):
		return True

	def displayString(self):
		return self['recipientEmail']



class ZipmarkPaymentMethod(PaymentBase):
	tableName = 'zipmarkPaymentMethod'
	columns = {
		'id': None,
		'vendorID': None,
		'vendorSecret': None,
		'recipientName': None,
		'recipientEmail': None
	}
	
	def getPublicDict(self):
		return OrderedDict([
			('id', self['id']),
			('type', self.tableName),
			('vendorID', self['vendorID']),
			('vendorSecret', self['vendorSecret']),
			('recipientName', self['recipientName']),
			('recipientEmail', self['recipientEmail'])
		])
	
	def canReceivePayment(self):
		return self['vendorID'] is not None and self['vendorSecret'] is not None

	def canSendPayment(self):
		return True

	def displayString(self):
		return self['recipientEmail']

