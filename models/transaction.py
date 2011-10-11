from tools.orm import *
from collections import OrderedDict
from datetime import datetime

import bcrypt
import hashlib
import logging



# -------------------------------------------------------------------
# Transactions
# -------------------------------------------------------------------

class Transaction(MappedObj):
	
	def __init__(self):
		self.id = None
		self.phaseID = None # @todo: make this a unique index (can't pay twice on a phase)
		self.senderID = None
		self.recipientID = None
		self.paymentMethodID = None
		self.amount = None
		self.dateInitiated = None
		self.dateApproved = None
		self.dateDeclined = None
	
	@classmethod
	def tableName(clz):
		return "transaction"
	
	@classmethod
	def iteratorWithSenderID(clz, senderID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE senderID = %%s"
			cursor.execute(query % clz.tableName(), senderID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def iteratorWithRecipientID(clz, recipientID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE recipientID = %%s"
			cursor.execute(query % clz.tableName(), recipientID)
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def iteratorWithSenderIDAndRecipientID(clz, senderID, recipientID):
		with Database() as (conn, cursor):
			query = """SELECT * FROM %s WHERE senderID = %%s 
				AND recipientID = %%s"""
			cursor.execute(query % clz.tableName(), (senderID, recipientID))
			result = cursor.fetchone()
			while result:
				yield clz.initWithDict(result)
				result = cursor.fetchone()
	
	@classmethod
	def retrieveByPhaseID(clz, phaseID):
		with Database() as (conn, cursor):
			query = "SELECT * FROM %s WHERE phaseID = %%s"
			cursor.execute(query % clz.tableName(), phaseID)
			result = cursor.fetchone()
			return clz.initWithDict(result)
