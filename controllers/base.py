# WurkHappy Base Encoding and Decoding Classes
# -------------------------------------------------------------------
# A collection of classes for converting numeric data and text
# representations back and forth for moving data. Includes
# implementations of Base16, Doug Crockford's Base32, and Flickr's
# Base58 encodings.
# 
# Version 0.1
# 
# Written by Brendan Berg
# Copyright WurkHappy, 2011



class BaseTranscoder(object):
	#TODO: modify so internal canonical representation is a byte array so it
	# can accept a Base64 digest
	
	alphabet = ''
	base = 0
	
	def __init__(self, obj):
		if isinstance(obj, int) or isinstance(obj, long):
			self.value = obj
			self.string = self._encode()
		elif isinstance(obj, BaseTranscoder):
			self.value = obj.value
			self.string = self._encode()
		elif isinstance(obj, str):
			self.string = self._canonicalRepr(obj)
			self.value = self._decode(self.string)
		else:
			raise ValueError('expected either Base instance, number, or string')
	
	def _encode(self):
		num = self.value
		encoded = ''
		
		while num > 0:
			pos = num % self.base
			num /= self.base
			encoded = self.alphabet[pos] + encoded
		
		self.string = encoded
		return encoded
	
	def _decode(self, stringRepr):
		decoded = 0
		
		for digit in stringRepr:
			decoded *= self.base
			decoded += self.alphabet.index(digit)
		
		return decoded
	
	def _canonicalRepr(self, string):
		string = string.upper()
		
		for k, v in self.replacements.iteritems():
			string = string.replace(k, v)
		
		return string
	
	def longValue(self):
		# decode bytes to int
		return self.value
	
	def __str__(self):
		return self.string or self._encode()



class Base16(BaseTranscoder):
	alphabet = '0123456789ABCDEF'
	base = 16
	replacements = {
		'-': '',
		' ': '',
		'I': '1',
		'L': '1',
		'O': '0',
	}


class Base32(BaseTranscoder):
	'''Class for Doug Crockford's Base32 encoding. This is not merely
	Python's `int(encoded, 32)` since Crockford's spec discusses replacements
	for commonly confused characters, rather than a simple extension of the
	alphabet used in hexadecimal. For example, the capital letter I, lower
	case i, and lower case l could all be mistaken for the numeral 1. This
	encoding removes that ambiguity by accepting any of these characters but
	converting to a canonical representation for decoding.
	
	http://www.crockford.com/wrmg/base32.html
	'''
	
	alphabet = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'
	base = 32
	replacements = {
		'-': '',
		' ': '',
		'I': '1',
		'L': '1',
		'O': '0',
	}


class Base58(BaseTranscoder):
	'''Class for Flickr's base 58 encoding. Base 58 encoding is similar to
	base 32, but includes upper and lower case letters. Upper case I, lower
	case l, and upper case O are all excluded from the alphabet. Like
	Crockford's base 32, base 58 encoding is accepting of ambiguous input.
	
	http://www.flickr.com/groups/api/discuss/72157616713786392
	'''
	
	alphabet = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
	base = 58
	replacements = {
		'-': '',
		' ': '',
		'I': '1',
		'l': '1',
		'O': 'o',
		'0': 'o'
	}
