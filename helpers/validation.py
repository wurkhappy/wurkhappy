# WurkHappy Helpers
# Version 0.1
# 
# Written by Brendan Berg
# Copyright Plus or Minus Five, 2011

import re


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

class Validation (object):
	@staticmethod
	def validateEmail(email):

		if len(email) > 7:
			if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
				return True
		return False

	@staticmethod
	def validateURL(URL):
		if re.match("^(http(?:s)?\:\/\/[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,6}(?:\/?|(?:\/[\w\-]+)*)(?:\/?|\/\w+\.[a-zA-Z]{2,4}(?:\?[\w]+\=[\w\-]+)?)?(?:\&[\w]+\=[\w\-]+)*)$", URL) != None:
			return True
		else:
			return False
