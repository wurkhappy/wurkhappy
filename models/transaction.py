from controllers.orm import *
from collections import OrderedDict
from datetime import datetime

import bcrypt
import hashlib
import logging



# -------------------------------------------------------------------
# Transactions
# -------------------------------------------------------------------

class Transaction(MappedObj):
	tableName = 'transaction'
	columns = {
		'id': None,
		'agreementPhaseID': None,
		'senderID': None, # fromClientID
		'recipientID': None, # toVendorID
		'paymentMethodID': None,
		'amount': None,
		'dateInitiated': None,
		'dateApproved': None,
		'dateDeclined': None,
		'dwollaTransactionID': None # Temporary until we use paymentMethods for this
	}
	
	@classmethod
	def iteratorWithSenderID(clz, senderID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE senderID = %%s"
			cursor.execute(query % clz.tableName, senderID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def iteratorWithRecipientID(clz, recipientID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE recipientID = %%s"
			cursor.execute(query % clz.tableName, recipientID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def iteratorWithSenderIDAndRecipientID(clz, senderID, recipientID):
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE senderID = %%s 
				AND recipientID = %%s"""
			cursor.execute(query % clz.tableName, (senderID, recipientID))
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def iteratorWithAgreementID(clz, agreementID):
		with Database() as (conn, cursor):
			query = """SELECT t.* FROM %s AS t
				LEFT JOIN agreementPhase AS p ON t.agreementPhaseID = p.id
				LEFT JOIN agreement AS a ON p.agreementID = a.id
				WHERE p.agreementID = %%s ORDER BY p.phaseNumber"""
			cursor.execute(query % clz.tableName, agreementID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def retrieveByAgreementPhaseID(clz, phaseID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE agreementPhaseID = %%s"
			cursor.execute(query % clz.tableName, phaseID)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	def getPublicDict(self):
		return OrderedDict([
			('id', self['id']),
			('senderID', self['senderID']),
			('recipientID', self['recipientID']),
			('paymentMethodID', self['paymentMethodID']),
			('amount', self['amount'])
		])