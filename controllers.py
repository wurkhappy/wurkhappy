# WurkHappy Helpers
# Version 0.1
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2011

import hashlib
import base64
import uuid
import string
import random
import re

# -------------------------------------------------------------------
# Verification
# -------------------------------------------------------------------

class Verification (object):
	@staticmethod
	def __generateCode():
		alphabet = string.ascii_uppercase
		code = ''
		checksum = 0
		for i in range(5):
			digit = random.randrange(0, 25)
			checksum += digit * i
			code += alphabet[digit]
		code += alphabet[checksum % 26]
		return code
	
	@staticmethod
	def __generateHashDigest():
		rawDigest = hashlib.sha1(uuid.uuid4().get_bytes()).digest()
		return base64.urlsafe_b64encode(rawDigest)
	
	def __init__(self):
		self.hashDigest = self.__generateHashDigest()
		self.code = self.__generateCode()
	
	@staticmethod
	def checkCode(code):
		alphabet = string.ascii_uppercase
		checksum = 0
		body = code[:-1]
		for index, digit in zip(range(len(body)), body):
			checksum += string.index(alphabet, digit) * index
		return string.index(alphabet, code[-1]) == checksum % 26
		
# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

import re
class Validation (object):
	@staticmethod
	def validateEmail(email):

		if len(email) > 7:
			if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
				return True
		return False