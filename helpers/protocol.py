from tornado.web import HTTPError

from collections import defaultdict
try:
	import json
except:
	import simplejson as json

class HTTPErrorBetter(HTTPError):
	def __init__(self, status_code, log_message, body_content, *args):
		super(HTTPError, self).__init__(status_code, log_message, *args)
		self.body_content = body_content



class ParamParser(object):
	
	def __init__(self, args, required=[], optional=[]):
		self.args = {}
		
		# Traverse optional list, populate dict
		# Traverse required list, populate dict
		# If required list has any items, raise an error
		
		err = []
		
		for t in optional:
			if len(t) != 2:
				HTTPError(500, "Optional arguments must contain a name and a protocol.")
			
			(name, protocol) = t
			
			try:
				self.args[name] = protocol << args.get(name, [None])[0]
			except Exception as e:
				err.append("'%s' parameter %s" % (name, e))
			
		req = []
		
		# tempGr = defaultdict(lambda: [])
		# groups = {}
		# protos = {}
		# 
		# for proto in required:
		# 	if len(proto) == 3:
		# 		tempGr[proto[2]].append(proto[0])
		# 
		# for group, names in tempGr.iteritems():
		# 	
		# 
		# 	else:
		# 		groups[proto[0]].append(proto[0])
		# err = []
		# 
		# for name, protocol in req.iteritems():
		# 	try:
		# 		if args.get(name, [None])[0] in protocol:
		# 			self.args[name] = protocol.val
		# 			del(req[name])
		# 		else:
		# 			err.append("'%s' parameter is malformed" % name)
		# 	except:
		# 		err.append("'%s' parameter is malformed" % name)
		# 
		# for proto in optional:
		# 	if len(proto) 
		# 	try:
		# 		if args.get(name, [None])[0] in protocol:
		# 			self.args[name] = protocol.val
		# 		else:
		# 			err.append("'%s' parameter is malformed" % name)
		# 	except:
		# 		err.append("'%s' parameter is malformed" % name)
		# 
		# err += ["'" + x + "' parameter is required" for x in req.keys()]
		# 
		if len(err):
			error = {
				"domain": "web.request",
				"debug": err
			}
			raise HTTPErrorBetter(400, "Error parsing request arguments", json.dumps(error))
	
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
		try:
			val = self.type(value) if value != None else self.default
		except TypeError, e:
			raise Exception("value must be type '%s'" % self.type.__name__)
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
	def inSet(st):
		return lambda x: x in st
	
	try:
		p = ParamParser({"one": ["1"], "three": ["tres"]},
		# required={
		# 			"four": Protocol(str)
		# 		},
		optional=[
			("one", PositiveInteger(int)),
			("two", Protocol(int, default=4)),
			("three", StringInSet(["uno","dos","tres"]))
		])
		print "----"
		print "one", p["one"], type(p["one"])
		print "two", p["two"], type(p["two"])
		print "three", p["three"], type(p["three"])
	except HTTPErrorBetter, e:
		print e.body_content
	
