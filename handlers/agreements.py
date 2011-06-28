import re

from base import *
from models.user import User
from models.agreement import Agreement
from models.agreement import AgreementTxn
from models.agreement import AgreementTxt
from models.profile import Profile

# -------------------------------------------------------------------
# Profile (Add / Edit)
# -------------------------------------------------------------------

class AgreementsHandler(Authenticated, BaseHandler):
	ERR = {
			"name_missing":"All name fields are required.",
			"invalid_url":"URLs must be of the format http://website.com."
	}
	
	def get(self, withWhom):	
		
		agreements = [
			("Waiting for Agreement", [{
				"name": "Performable - Updating Application",
				"client_name": "Joe Smith",
				"date": "April 12, 2011",
				"amount": "$6,400"
			}]),
			("Waiting for Verification", [{
				"name": "Atheneum Learning - Marketing Website",
				"client_name": "Joe Smith",
				"date": "April 12, 2011",
				"amount": "$6,400"
			}]),
			("In Progress", [{
				"name": "Performable - Updating Application",
				"client_name": "Joe Smith",
				"date": "April 12, 2011",
				"amount": "$6,400"
			}, 	{
				"name": "Atheneum Learning - Marketing Website",
				"client_name": "Joe Smith",
				"date": "April 12, 2011",
				"amount": "$6,400"
			}, 	{
				"name": "Performable - Updating Application",
				"client_name": "Joe Smith",
				"date": "April 12, 2011",
				"amount": "$6,400"
			}])
		]
		
		
		self.render("agreement/list.html", title="Vendor Agreements &ndash; Wurk Happy", agreement_groups=agreements)
		