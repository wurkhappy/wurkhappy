


# -------------------------------------------------------------------
# State Transition Error
# -------------------------------------------------------------------

class StateTransitionError(AssertionError):
	'''
	Exception class for state machine transition errors
	'''

	def __init__(self, message, type):
		AssertionError.__init__(self, message)
		self.type = type



# -------------------------------------------------------------------
# Database Errors
# -------------------------------------------------------------------

class DatabaseConnectionError(Exception):
	pass



