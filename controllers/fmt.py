from __future__ import division
from tornado.web import HTTPError

from collections import defaultdict
import json
import re
import logging

from datetime import datetime

class HTTPErrorBetter(HTTPError):
	def __init__(self, status_code, log_message, body_content, *args):
		HTTPError.__init__(self, status_code, log_message, *args)
		self.body_content = body_content



# Possibly a weirdo thing: Distinguishing between scalar and array types.
# Each Enforcer subclass should unpack values? That way a list will always be
# retrieved by the Parser and sent to the Enforcer, and the Enforcer is
# responsible for massaging it into the correct type.

class Parser(object):
	
	def __init__(self, args, required=[], optional=[]):
		self.args = {}
		
		# Traverse optional list, populate dict
		# Traverse required list, populate dict
		# If required list is missing any items, raise an error
		
		err = []
		
		for t in required:
			if len(t) != 2:
				raise HTTPError(500, "Argument specifications must contain a name and a protocol.")
			
			(name, protocol) = t
			
			if name not in args:
				err.append("'%s' parameter is required" % name)
				continue
			
			try:
				self.args[name] = protocol << args[name]
			except Exception as e:
				err.append("'%s' parameter %s" % (name, e))
			
		for t in optional:
			if len(t) != 2:
				raise HTTPError(500, "Argument specifications must contain a name and a protocol.")
			
			(name, protocol) = t
			
			try:
				self.args[name] = protocol << args.get(name, None)
			except Exception as e:
				err.append("'%s' parameter %s" % (name, e))
		
		if len(err):
			error = {
				"domain": "web.request",
				"debug": err
			}
			raise HTTPErrorBetter(400, "Error parsing request arguments", json.dumps(error))
	
	def iteritems(self):
		return self.args.iteritems()
	
	def __len__(self):
		return len(self.args)
	
	def __getitem__(self, name):
		return self.args[name]
	
	def __contains__(self, name):
		return name in self.args



# -------------------------------------------------------------------
# Protocols (Sublcasses of `Enforce`)
# -------------------------------------------------------------------

class Enforce(object):
	inRange = lambda mn, mx: (lambda x: x >= mn and x <= mx)
	inSet = lambda st: (lambda x: x in st)
	
	def test(self, value):
		pass
	
	def __init__(self, dataType=str, default=None):
		self.type = dataType
		self.default = default
	
	def __lshift__(self, value):
		if value is None:
			return self.default
		
		try:
			val = self.type(value[0])
		except TypeError as e:
			raise Exception("value cannot be converted to type '%s'" % self.type.__name__)
		
		self.test(val)
		return val



class List(Enforce):
	def __init__(self, protocol=Enforce(str), default=[]):
		Enforce.__init__(self, list, default)
		self.protocol = protocol
	
	def __lshift__(self, value):
		if value is None:
			return self.default
		
		val = []
		
		for item in value:
			# The enforcer class expects a list, so we make one.
			# Otherwise we end up with a truncated string.
			val.append(self.protocol << [item])
		
		return val



class PositiveInteger(Enforce):
	def __init__(self, default=None):
		Enforce.__init__(self, int, default)
	
	def test(self, value):
		if value < 0:
			raise Exception("value must be a positive integer")



class IntegerInRange(Enforce):
	def __init__(self, r, default=None):
		Enforce.__init__(self, int, default)
		self.range = r
	
	def test(self, value):
		if value not in self.range:
			raise Exception("value must be an integer between %d and %d" % (min(self.range), max(self.range)))



class Boolean(Enforce):
	def __init__(self, default=False):
		Enforce.__init__(self, bool, default)
	
	def filter(self, value):
		if value.lower() in ['true', 't', 'yes', 'y']:
			return True
		elif value.lower() in ['false', 'f', 'no', 'n']:
			return False
		else:
			raise Exception("boolean values must be either 'true' or 'false'")
	
	def __lshift__(self, value):
		if value is None:
			return self.default

		return self.filter(value[0])



class String(Enforce):
	def __init__(self, r=[None, None], default=None):
		Enforce.__init__(self, str, default)
		self.range = r
	
	def filter(self, value):
		length = len(value)

		if self.range[0] is not None and length < self.range[0]:
			raise Exception("value must have at least {0} characters".format(self.range[0]))

		if self.range[1] is not None and length >= self.range[1]:
			raise Exception("value must not exceed {0} characters".format(self.range[0]))

		return value
	
	def __lshift__(self, value):
		if value is None:
			return self.default

		return self.filter(value[0])



class StringInSet(Enforce):
	def __init__(self, s, default=None):
		Enforce.__init__(self, str, default)
		self.set = s

	def test(self, value):
		if value not in self.set:
			raise Exception("value must be one of %s" % ", ".join(["'%s'" % x for x in self.set]))



class Email(Enforce):
	def __init__(self, default=None):
		Enforce.__init__(self, str, default)
	
	def test(self, value):
		if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', value):
			raise Exception("value must be well-formed")
	
	def __lshift__(self, value):
		if value is None:
			return self.default
		
		self.test(value[0])
		return value[0].lower()



class URL(Enforce):
	def __init__(self, default=None):
		Enforce.__init__(self, str, default)
	
	# TODO: unit test this
	def test(self, value):
		if not re.match(r'^(http(?:s)?://[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,6}(?:/?|(?:/[\w\-]+)*)(?:/?|/\w+\.[a-zA-Z]{2,4}(?:\?[\w]+\=[\w\-]+)?)?(?:\&[\w]+\=[\w\-]+)*)$', value):
			raise Exception("value must be well-formed")



class Currency(Enforce):
	def __init__(self, r=[None, None], default=None):
		Enforce.__init__(self, int, default)
		self.range = r
	
	def filter(self, value):
		r = re.compile(r'\$?([0-9,]+)(?:\.([0-9]{2}))?')
		m = r.match(value)
		if not m or len(m.groups()) != 2:
			raise Exception("value must be well-formed")
		
		d = int(m.groups()[0].replace(',', '')) * 100
		
		if m.groups()[1]:
			d += int(m.groups()[1])
		
		if self.range[0] is not None and d < self.range[0]:
			raise Exception("value must be greater than ${0:,.2f}".format(self.range[0] / 100))
		
		if self.range[1] is not None and d > self.range[1]:
			raise Exception("value must be less than ${0:,.2f}".format(self.range[1] / 100))
		
		return d
	
	def __lshift__(self, value):
		if value is None or str(value[0]) is '':
			return self.default
		
		return self.filter(value[0])
		
class PhoneNumber(Enforce):
	def __init__(self, default=None):
		Enforce.__init__(self, str, default)
	
	def filter(self, value):
		for ch in "() -.":
			value = value.replace(ch, '')
		
		match = re.match(r'^(?:\+1 ?)?([0-9]{10})$', value)
		if not match:
			raise Exception("value must be well-formed")
		
		val = match.groups()[0]
		return '(%s) %s-%s' % (val[0:3], val[3:6], val[6:10])
	
	def __lshift__(self, value):
		if value is None or str(value[0]) is '':
			return self.default

		try:
			val = self.type(value[0])
		except TypeError as e:
			raise Exception("value cannot be converted to type '%s'" % self.type.__name__)

		return self.filter(val)

class Date(Enforce):
	def __init__(self, default=None):
		Enforce.__init__(self, datetime, default)
	
	def filter(self, value):
		logging.warn(value)
		
		r = re.compile(r'^([0-9]{4})-([0-9]{2})-([0-9]{2})$')
		match = r.match(value)
		
		if not match:
			raise Exception("value must be well-formed")
		
		logging.warn(match.groups())
		parts = match.groups()
		d = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
		return d
	
	def __lshift__(self, value):
		if value is None or str(value[0]) is '':
			return self.default
		
		return self.filter(value[0])

if __name__ == "__main__":
	try:
		p = Parser({"one": ["146"], "three": ["tres"], "four": ["foo"], "five": ["23623"]},
		required=[
			("four", Enforce(str)),
			("five", Enforce(int))
		],
		optional=[
			("one", PositiveInteger(int)),
			("two", Enforce(int, default=4)),
			("three", StringInSet(["uno","dos","tres"]))
		])
		print "----"
		for k, v in p.iteritems():
			print k, "(%s)" % type(v).__name__, v
		
	except HTTPErrorBetter, e:
		print e.body_content
	
