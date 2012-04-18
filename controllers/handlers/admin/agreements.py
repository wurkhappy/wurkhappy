from tornado import web
from base import BaseHandler, Authenticated
from models.agreement import Agreement
from controllers import fmt

import logging

class AgreementListHandler(BaseHandler, Authenticated):
	@web.authenticated
	def get(self):
		admin = self.current_user
		
		try:
			args = fmt.Parser(self.get_arguments,
				optional=[
					('offset', fmt.PositiveInteger(default=0)),
					('limit', fmt.IntegerInRange(range(5, 50), default=20))
				],
				required=[]
			)
		except:
			self.set_status(400)
			return
		
		agreements = list(Agreement.iteratorWithPage((offset, limit)))
		data = [u.getPublicDict() for u in agreements]
		self.render('agreement/list.html', data=data)



class AgreementDetailHandler(BaseHandler, Authenticated):
	@web.authenticated
	def get(self, userID):
		admin = self.current_user
		
		agreement = Agreement.retrieveByID(userID)
		
		if not agreement:
			self.set_status(404)
			return
		
		data = agreement.getPublicDict()
		data['state'] = agreement.getCurrentState()
		self.render('agreement/detail.html', data=data)


