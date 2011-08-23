from __future__ import division

from base import *
from models.user import User
import json
from datetime import datetime
import logging
import os

class FileHandler(BaseHandler, Authenticated):
	def post(self):
		user = User.retrieveByID(1)
		fileDict = self.request.files['file'][0]
		base, ext = os.path.splitext(fileDict['filename'])
		user.setProfileImage(fileDict['body'], ext, {'Content-Type': fileDict['content_type']})