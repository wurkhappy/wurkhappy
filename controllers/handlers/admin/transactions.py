from tornado import web
from base import BaseHandler, Authenticated
from models.user import User, UserPrefs
from models.transaction import Transaction
from models.agreement import Agreement, AgreementPhase
from controllers import fmt
from controllers.beanstalk import Beanstalk

from datetime import datetime
import logging
import json



class TransactionListHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		admin = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('recipient_id', fmt.PositiveInteger()),
					('sender_id', fmt.PositiveInteger()),
					('offset', fmt.PositiveInteger(default=0)),
					('limit', fmt.IntegerInRange(range(5, 50), default=20))
				],
				required=[]
			)
		except Exception as e:
			logging.error(e)
			self.set_status(400)
			return
		
		offset = args['offset']
		limit = args['limit']
		
		transactions = []
		
		if args['recipient_id']:
			transactions = list(Transaction.iteratorWithRecipientIDAndPage(args['recipient_id'], (offset, limit)))
		elif args['sender_id']:
			transactions = list(Transaction.iteratorWithSenderIDAndPage(args['sender_id'], (offset, limit)))
		
		if len(transactions) == 0:
			transactions = list(Transaction.iteratorWithPage((offset, limit)))
		
		data = {'transactions': []}
		
		for transaction in transactions:
			t = transaction.getPublicDict()
			s = User.retrieveByID(t['senderID'])
			r = User.retrieveByID(t['recipientID'])
			p = AgreementPhase.retrieveByID(t['agreementPhaseID'])
			
			t['sender'] = s and s.getPublicDict()
			t['recipient'] = r and r.getPublicDict()
			t['agreementPhase'] = p and p.getPublicDict()
			
			if p:
				a = Agreement.retrieveByID(p['agreementID'])
				t['agreementPhase']['agreement'] = a and a.getPublicDict()
				# del(t['agreementPhase']['agreementID'])
			
			del(t['senderID'])
			del(t['recipientID'])
			del(t['agreementPhaseID'])
			
			data['transactions'].append(t)
		
		hostname = self.application.configuration['admin']['hostname']
		
		data['next'] = '{0}://{1}/transactions?offset={2}&limit={3}'.format(
			self.request.protocol, hostname, offset+limit, limit
		) if offset + (limit) < Transaction.count() else None
		
		data['prev'] = '{0}://{1}/transactions?offset={2}&limit={3}'.format(
			self.request.protocol, hostname, offset-limit, limit
		) if offset else None
		
		self.render('transaction/list.html', data=data, title='Admin &ndash; Transactions')



class TransactionDetailHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self, transactionID):
		admin = self.current_user
		
		transaction = Transaction.retrieveByID(transactionID)
		
		if not transaction:
			self.set_status(404)
			return
		
		data = transaction.getPublicDict()
		
		s = User.retrieveByID(transaction['senderID'])
		r = User.retrieveByID(transaction['recipientID'])
		p = AgreementPhase.retrieveByID(transaction['agreementPhaseID'])
	
		data['sender'] = s and s.getPublicDict()
		data['recipient'] = r and r.getPublicDict()
		data['agreementPhase'] = p and p.getPublicDict()
		
		if p:
			a = Agreement.retrieveByID(p['agreementID'])
			data['agreementPhase']['agreement'] = a and a.getPublicDict()
			# del(data['agreementPhase']['agreementID'])
		
			del(data['senderID'])
			del(data['recipientID'])
			del(data['agreementPhaseID'])
		
		data['_xsrf'] = self.xsrf_token
		self.render('transaction/detail.html', data=data, title='Admin &ndash; Transaction Detail')
