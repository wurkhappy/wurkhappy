from tornado.web import HTTPError

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
		
		req = []
		
		groups = {}
		protos = {}
		
		for proto in required:
			if len(proto) == 3:
				
		err = []
		
		for name, protocol in req.iteritems():
			try:
				if args.get(name, [None])[0] in protocol:
					self.args[name] = protocol.val
					del(req[name])
				else:
					err.append("'%s' parameter is malformed" % name)
			except:
				err.append("'%s' parameter is malformed" % name)
		
		for proto in optional:
			if len(proto) 
			try:
				if args.get(name, [None])[0] in protocol:
					self.args[name] = protocol.val
				else:
					err.append("'%s' parameter is malformed" % name)
			except:
				err.append("'%s' parameter is malformed" % name)
		
		err += ["'" + x + "' parameter is required" for x in req.keys()]
		
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



class Protocol(object):
	inRange = lambda mn, mx: (lambda x: x >= mn and x <= mx)
	inSet = lambda st: (lambda x: x in st)
	
	def __init__(self, dataType, check=None, default=None):
		self.type = dataType
		self.check = check
		self.default = default
	
	def __contains__(self, value):
		self.val = self.type(value) if value else self.default
		return self.check(self.type(self.val)) if self.check else True


if __name__ == "__main__":
	def inSet(st):
		return lambda x: x in st
	
	try:
		p = ParamParser({"one": ["j"], "three": ["tres"]}, required={
			"four": Protocol(str)
		},
		optional={
			"one": Protocol(int),
			"two": Protocol(str),
			"three": Protocol(str, inSet(["uno","dos","tres"]))
		})
		print "----"
		print "one", p["one"], type(p["one"])
		print "two", p["two"], type(p["two"])
		print "three", p["three"], type(p["three"])
	except HTTPErrorBetter, e:
		print e.body_content
	
