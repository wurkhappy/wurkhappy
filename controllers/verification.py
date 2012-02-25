import hashlib
# import base64
import uuid
import string
import random
import hmac
import os
import smtplib
import bcrypt

#from base import Base16, Base58
from data import Data, Base58

# -------------------------------------------------------------------
# Verification
# -------------------------------------------------------------------

class Verification (object):
	def __init__(self):
		self.hashDigest = self.generateHashDigest()
		self.code = self.generateCode()
	
	@staticmethod
	def generateCode():
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
	def generateHashDigest():
		digest = hashlib.sha1(uuid.uuid4().bytes).digest()
		return Data(digest).stringWithEncoding(Base58)
	
	@staticmethod
	def checkCode(code):
		alphabet = string.ascii_uppercase
		checksum = 0
		body = code[:-1]
		for (index, digit) in enumerate(body):
			checksum += string.index(alphabet, digit) * index
		return string.index(alphabet, code[-1]) == checksum % 26
	# 
	# @staticmethod
	# def hash_password(plain_password):
	# 	# default log_rounds is 12
	# 	return bcrypt.hashpw(plain_password, bcrypt.gensalt())
	# 
	# @staticmethod
	# def check_password(hashedPassword, plainPassword):
	# 	return hashedPassword == bcrypt.hashpw(plainPassword, hashedPassword)
	# 
	# @staticmethod
	# def passwordIsValid(hashedPassword, plainPassword):
	# 	return hashedPassword == bcrypt.hashpw(plainPassword, hashedPassword)

