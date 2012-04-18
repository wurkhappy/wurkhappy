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
		'display': None,
		'cardExpires': None,
		'abaDisplay': None,
		'gatewayToken': None,
		'dateDeleted': None
	}
	
	@classmethod
	def retrieveCCMethodWithUserID(clz, userID):
		# Credit card payment method records don't have ABA routing info
		# to display, so we'll assume for now that if the field is null we've
		# got a credit card record.
		
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE userID = %%s
				AND abaDisplay is NULL AND dateDeleted is NULL LIMIT 1"""
			cursor.execute(query % clz.tableName, userID)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	@classmethod
	def retrieveACHMethodWithUserID(clz, userID):
		# ACH payment methods don't have a card expiration date, so that's
		# how we filter for ACH records
		
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE userID = %%s
				AND cardExpires is NULL AND dateDeleted is NULL LIMIT 1"""
			cursor.execute(query % clz.tableName, userID)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	def getPublicDict(self):
		d = OrderedDict([
			('id', self['id']),
			('userID', self['userID']),
			('display', self['display'])
		])
		
		if self['abaDisplay'] is None:
			d['cardExpires'] = self['cardExpires']
			d['type'] = 'CC'
		elif self['cardExpires'] is None:
			d['abaDisplay'] = self['abaDisplay']
			d['type'] = 'ACH'
		
		return d

