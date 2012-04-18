from tornado import web
from base import BaseHandler, Authenticated
from models.user import User, UserPrefs
from controllers import fmt
from controllers.beanstalk import Beanstalk

from datetime import datetime
import logging
import json

class UserListHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self):
		admin = self.current_user
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
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
		
		users = list(User.iteratorWithPage((offset, limit)))
		data = { 'users': [] }
		
		for user in users:
			u = user.getPublicDict()
			u['state'] = user.getCurrentState()
			data['users'].append(u)
		
		hostname = self.application.configuration['admin']['hostname']
		
		data['next'] = '{0}://{1}/users?offset={2}&limit={3}'.format(
			self.request.protocol, hostname, offset+limit, limit
		) if offset + (limit) < User.count() else None
		
		data['prev'] = '{0}://{1}/users?offset={2}&limit={3}'.format(
			self.request.protocol, hostname, offset-limit, limit
		) if offset else None
		
		self.render('user/list.html', data=data, title='Admin &ndash; Users')



class UserDetailHandler(Authenticated, BaseHandler):
	@web.authenticated
	def get(self, userID):
		admin = self.current_user
		
		user = User.retrieveByID(userID)
		
		if not user:
			self.set_status(404)
			return
		
		data = user.getPublicDict()
		
		if user['invitedBy']:
			sender = User.retrieveByID(user['invitedBy'])
			data['invitedBy'] = sender.getPublicDict()
			data['invitedBy']['url'] = 'http://{0}/user/{1}'.format(self.request.host, sender['id'])
		else:
			data['invitedBy'] = None
		
		data['_xsrf'] = self.xsrf_token
		data['fields'] = user.fields
		data['preferences'] = [p.getPublicDict() for p in UserPrefs.iteratorWithUserID(user['id'])]
		data['state'] = user.getCurrentState()
		self.render('user/detail.html', data=data, title='Admin &ndash; User Detail')



class UserActionJSONHandler(Authenticated, BaseHandler):
	@web.authenticated
	def post(self, userID):
		admin = self.current_user
		
		user = User.retrieveByID(userID)
		
		if not user:
			self.set_status(400)
			return
		
		try:
			args = fmt.Parser(self.request.arguments,
				optional=[
					('action', fmt.Enforce(str))
				],
				required=[]
			)
		except Exception as e:
			logging.error(e)
			self.set_status(400)
			return
		
		if args['action'] == 'send_invitation':
			msg = {
				'action': 'userInvite',
				'userID': user['id']
			}
		elif args['action'] == 'send_password_reset':
			msg = {
				'action': 'userResetPassword',
				'userID': user['id']
			}
		elif args['action'] == 'lock_account':
			msg = None
			user['dateLocked'] = datetime.now()
			user.save()
		elif args['action'] == 'unlock_account':
			msg = None
			user['dateLocked'] = None
			user.save()
		else:
			self.set_status(400)
			return
		
		if msg:
			with Beanstalk() as bconn:
				tube = self.application.configuration['notifications']['beanstalk_tube']
				bconn.use(tube)
				r = bconn.put(json.dumps(msg))
				logging.info('Beanstalk: %s#%d %s' % (tube, r, msg))
		
		self.renderJSON(user.getPublicDict())
