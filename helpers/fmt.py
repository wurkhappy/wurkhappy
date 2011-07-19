from tornado.web import HTTPError

from collections import defaultdict
try:
	import json
except:
	import simplejson as json

class HTTPErrorBetter(HTTPError):
	def __init__(self, status_code, log_message, body_content, *args):
		HTTPError.__init__(self, status_code, log_message, *args)
		self.body_content = body_content



class Parser(object):
	
	def __init__(self, args, required=[], optional=[]):
		self.args = {}
		
		# Traverse optional list, populate dict
		# Traverse required list, populate dict
		# If required list has any items, raise an error
		
		err = []
		
		for t in required:
			if len(t) != 2:
				raise HTTPError(500, "Argument specifications must contain a name and a protocol.")
			
			(name, protocol) = t
			
			if name not in args:
				err.append("'%s' parameter is required" % name)
				continue
			
			try:
				self.args[name] = protocol << args[name][0]
			except Exception as e:
				err.append("'%s' parameter %s" % (name, e))
			
		for t in optional:
			if len(t) != 2:
				raise HTTPError(500, "Argument specifications must contain a name and a protocol.")
			
			(name, protocol) = t
			
			try:
				self.args[name] = protocol << args.get(name, [None])[0]
			except Exception as e:
				err.append("'%s' parameter %s" % (name, e))
			
		req = []
		
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
# Protocols
# -------------------------------------------------------------------

class Protocol(object):
	inRange = lambda mn, mx: (lambda x: x >= mn and x <= mx)
	inSet = lambda st: (lambda x: x in st)
	
	def test(self, value):
		pass
	
	def __init__(self, dataType=str, default=None):
		self.type = dataType
		self.default = default
	
	def __lshift__(self, value):
		if value == None:
			return self.default
		
		try:
			val = self.type(value)
		except TypeError as e:
			raise Exception("value cannot be converted to type '%s'" % self.type.__name__)
		
		self.test(val)
		return val



class PositiveInteger(Protocol):
	def __init__(self, default=None):
		Protocol.__init__(self, int, default)
	
	def test(self, value):
		if value < 0:
			raise Exception("value must be a positive integer")



class IntegerInRange(Protocol):
	def __init__(self, r, default=None):
		Protocol.__init__(self, int, default)
		self.range = r
	
	def test(self, value):
		if value not in self.range:
			raise Exception("value must be an integer between %d and %d" % (min(self.range), max(self.range)))



class StringInSet(Protocol):
	def __init__(self, s, default=None):
		Protocol.__init__(self, str, default)
		self.set = s

	def test(self, value):
		if value not in self.set:
			raise Exception("value must be one of %s" % ", ".join(["'%s'" % x for x in self.set]))



if __name__ == "__main__":
	try:
		p = Parser({"one": ["146"], "three": ["tres"], "four": ["foo"], "five": ["23623"]},
		required=[
			("four", Protocol(str)),
			("five", Protocol(int))
		],
		optional=[
			("one", PositiveInteger(int)),
			("two", Protocol(int, default=4)),
			("three", StringInSet(["uno","dos","tres"]))
		])
		print "----"
		for k, v in p.iteritems():
			print k, "(%s)" % type(v).__name__, v
		
	except HTTPErrorBetter, e:
		print e.body_content
	