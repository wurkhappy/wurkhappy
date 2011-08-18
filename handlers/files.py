from __future__ import division

from base import *
from models.user import User
import json
from datetime import datetime
import logging

class FileHandler(BaseHandler, Authenticated):
	def post(self):
		user = User.retrieveByID(1)
		fileDict = self.request.files['file']
		user.setProfileImage(fileDict['body'])