# WurkHappy Data Models
# Version 0.1
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2011

import hashlib
import base64
import uuid
import string
import random

# -------------------------------------------------------------------
# Verification
# -------------------------------------------------------------------

class Verification (object):
	@staticmethod
	def _generateCode():
		alphabet = string.ascii_uppercase
		return ''.join(random.choice(alphabet) for x in range(6))
	
	@staticmethod
	def _generateHashDigest():
		rawDigest = hashlib.sha1(uuid.uuid4().get_bytes()).digest()
		return base64.urlsafe_b64encode(rawDigest)
	
	def __init__(self):
		self.hashDigest = self._generateHashDigest()
		self.code = self._generateCode()
	