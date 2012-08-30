


class WurkHappy(object):
	settings = {}
	
	@classmethod
	def configure(clz, settings, tag=None):
		clz.settings[tag] = settings
	
	@classmethod
	def getSettingWithTag(clz, name, tag=None):
		return clz.settings.get(tag, {}).get(name, None)
