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
		'transactionReference': None,
		'agreementPhaseID': None,
		'senderID': None, # fromClientID
		'recipientID': None, # toVendorID
		'paymentMethodID': None,
		'amount': None,
		'dateInitiated': None,
		'dateApproved': None,
		'dateDeclined': None,
		'amazonTransactionID': None,
		'amazonPaymentMethod': None
	}
	
	@classmethod
	def count(clz):
		with Database() as (conn, cursor):
			cursor.execute("SELECT COUNT(*) FROM {0}".format(clz.tableName))
			result = cursor.fetchone()
		
		return result['COUNT(*)']
	
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
	def iteratorWithRecipientIDAndPage(clz, recipientID, page):
		with Database() as (conn, cursor):
			query = "SELECT * FROM {0} WHERE recipientID = %s ORDER BY id ASC LIMIT %s, %s".format(clz.tableName)
			cursor.execute(query, (recipientID, page[0], page[1]))
			result = cursor.fetchone()

			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()

	@classmethod
	def iteratorWithSenderIDAndPage(clz, senderID, page):
		with Database() as (conn, cursor):
			query = "SELECT * FROM {0} WHERE senderID = %s ORDER BY id ASC LIMIT %s, %s".format(clz.tableName)
			cursor.execute(query, (senderID, page[0], page[1]))
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
	
	@classmethod
	def retrieveByTransactionReference(clz, txnRef):
		with Database() as (conn, cursor):
			query = "SELECT * FROM {0} WHERE transactionReference = %s"
			cursor.execute(query.format(clz.tableName), txnRef)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	@classmethod
	def retrieveByAgreementPhaseID(clz, phaseID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE agreementPhaseID = %%s"
			cursor.execute(query % clz.tableName, phaseID)
			result = cursor.fetchone()
			return clz.initWithDict(result)
	
	# TODO: refactor this into some 'amount'->'costString' mixin?
	def getCostString(self, prefix='$', default=''):
		return "{0}{1:,.2f}".format(prefix, self['amount'] / 100) if self['amount'] else default
	
	def getPublicDict(self):
		return OrderedDict([
			('id', self['id']),
			('transactionReference', self['transactionReference']),
			('agreementPhaseID', self['agreementPhaseID']),
			('senderID', self['senderID']),
			('recipientID', self['recipientID']),
			('paymentMethodID', self['paymentMethodID']),
			('costString', self.getCostString()),
			('dateInitiated', self['dateInitiated']),
			('dateApproved', self['dateApproved']),
			('dateDeclined', self['dateDeclined']),
			('amazonTransactionID', self['amazonTransactionID']),
			('amazonPaymentMethod', self['amazonPaymentMethod'])
		])