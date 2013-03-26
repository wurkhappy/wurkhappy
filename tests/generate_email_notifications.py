import tornado.template as template

from datetime import datetime

from controllers.verification import Verification
from models.agreement import Agreement
from models.user import User



class EmailNotificationTest(object):
	def __init__(self):
		self.loader = template.Loader('templates/notification')
	
	def generateHTMLOutput(self, agreement, client, vendor):
		t = self.loader.load('agreement_accept.html')

		data = {
			'hostname': 'fake.wurkhappy.com',
			'client': client,
			'vendor': vendor,
			'agreement': agreement
		}

		htmlString = t.generate(data=data)
		print(htmlString)



if __name__ == '__main__':
	client = dict(
		id=12345,
		email='client@clientco.com',

		firstName='Grace',
		lastName='Hopper',
		fullName='Grace Hopper',
		telephone='(212) 555-1212',
		profileSmallURL=None
	)

	vendor = dict(
		id=54321,
		
		email='vendor@vendorco.com',

		firstName='Ada',
		lastName='Lovelace',
		fullName='Ada Lovelace',
		telephone='(917) 555-1234',
		profileSmallURL=None
	)
	
	verify = Verification()

	agreement = dict(
		id=67890,
		vendorID=54321,
		clientID=12345,
		name='Example Agreement',
		costString='$1200.00',
		token='abcde',
		phases=[dict(
			phaseNumber=0,
			amount=60000,
			costString='$600.00',
			estimatedCompletion=datetime(2013, 03, 31),
			dateCompleted=None,
			dateVerified=None,
			dateContested=None,
			description='Phase One; Introduction',
			comments=None
		), dict(
			phaseNumber=1,
			amount=60000,
			costString='$600.00',
			estimatedCompletion=datetime(2013, 04, 30),
			dateCompleted=None,
			dateVerified=None,
			dateContested=None,
			description='Phase Two; Conclusion',
			comments=None
		)]
	)
	
	# agreement['tokenFingerprint'] = hashlib.md5(verify.hashDigest).hexdigest()
	# agreement['tokenHash'] = bcrypt.hashpw(str(verify.hashDigest), bcrypt.gensalt())
	
	notificationTester = EmailNotificationTest()
	notificationTester.generateHTMLOutput(agreement, client, vendor)

