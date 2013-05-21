from controllers.data import Data, Base64
from tornado.httpclient import HTTPClient, HTTPError

from datetime import datetime


class ZipmarkConnectionError(Exception):
	pass



class Zipmark(object):
	settings = {}

	@classmethod
	def configure(clz, settings, tag=None):
		clz.settings[tag] = settings
	
	@classmethod
	def getSettingWithTag(clz, name, tag=None):
		return clz.settings.get(tag, {}).get(name, None)

