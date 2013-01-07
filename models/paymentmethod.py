from controllers.orm import *
from collections import OrderedDict



# -------------------------------------------------------------------
# Payment Methods
# -------------------------------------------------------------------
# A payment method is record of stored payment info. Eventually we'll
# want to have much more granular contol over what's going on here.

class PaymentMethod(MappedObj):
	tableName = 'paymentMethod'
	columns = {
		'id': None,
		'userID': None,
		'dateDeleted': None,
		'oobPMID': None,
		'amazonPMID': None,
		'zipmarkPMID': None
	}
	



class PaymentBase(MappedObj):
	'''
	Base class for payment method types
	'''
	
	@classmethod
	def _retrieveByUserID(clz, userID):
		'''Helper method for the base class's `retrieveByUserID` method, which
		calls the helper on each subclass of the base class.'''

		with Database() as (conn, cursor):
			query = '''SELECT oob.* FROM {0} AS oob, {1} AS pm WHERE pm.userID = %s
				AND dateDeleted IS NULL AND pm.oobPMID = oob.id LIMIT 1'''
			cursor.execute(query.format(clz.tableName, PaymentMethod.tableName), userID)
			result = cursor.fetchone()
			return clz.initWithDict(result)

	@classmethod
	def retrieveByUserID(clz, userID):
		paymentMethods = []
		for pmClass in clz.__subclasses__():
			paymentMethods.append(pmClass._retrieveByUserID(userID))
		
		# IYI:
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
		
		return list(i for c in clz.__subclasses__() for i in c._retrieveByUserID(userID))
	
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



class AmazonPaymentMethod(PaymentBase):
	tableName = 'amazonPaymentMethod'
	columns = {
		'id': None,
		'tokenID': None,
		'tokenSecretID': None,
		'recipientEmail': None,
		'verificationComplete': None
	}

	def canReceivePayment(self):
		return self['verificationComplete'] == True

	def canSendPayment(self):
		return True



class ZipmarkPaymentMethod(PaymentBase):
	tableName = 'zipmarkPaymentMethod'
	columns = {
		'id': None
	}

	def canReceivePayment(self):
		return self['merchantID'] is not None

	def canSendPayment(self):
		return True

