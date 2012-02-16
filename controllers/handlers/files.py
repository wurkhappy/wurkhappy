from __future__ import division

from base import *
from models.user import User
import json
from datetime import datetime
import logging
import os

from StringIO import StringIO
import Image
import ImageOps

# from controllers.base import Base16, Base58
from controllers.data import Data, Base58

from hashlib import sha1
import uuid
from controllers.amazonaws import AmazonS3
from boto.s3.key import Key


class FileHandler(BaseHandler, Authenticated):
	def post(self):
		user = User.retrieveByID(1)
		fileDict = self.request.files['file'][0]
		base, ext = os.path.splitext(fileDict['filename'])
		
		imgs = {
			'o': None,
			's': None,
			'l': None
		}
		
		headers = {'Content-Type': fileDict['content_type']}
		
		try:
			imgs['o'] = Image.open(StringIO(fileDict['body']))
		except IOError as e:
			error = {
				'domain': 'web.request',
				'display': (
					"I'm sorry, that image was either damaged or unrecognized. "
					"Could you please try to upload it again?"
				),
				'debug': 'cannot identify image file'
			}
			
			raise HTTPErrorBetter(400, "Failed to read image", 
				json.dumps(error))
		
		imgs['s'] = ImageOps.fit(imgs['o'], (50, 50))
		imgs['l'] = ImageOps.fit(imgs['o'], (150, 150))
		
		# hashString = Base58(Base16(sha1(uuid.uuid4().bytes).hexdigest())).string
		digest = sha1(uuid.uuid4().bytes).digest()
		hashString = Data(digest).stringWithEncoding(Base58)
		nameFormat = '%s_%%s%s' % (hashString, ext)
		
		with AmazonS3() as (conn, bucket):
			for t, v in imgs.iteritems():
				imgData = StringIO()
				v.save(imgData, 'JPEG')
				
				k = Key(bucket)
				k.key = nameFormat % t
				k.set_contents_from_string(imgData.getvalue(), headers)
				k.make_public()
		
		# user.setProfileImage(fileDict['body'], ext, {'Content-Type': fileDict['content_type']})
	
	