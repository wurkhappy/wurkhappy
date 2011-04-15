import re

from base import *
from models.user import User
from models.project import Project
from models.invoice import Invoice
from helpers.verification import Verification
from helpers.validation import Validation


# ----------------------------------------------------------------------
# Invoice Handler
#
# GET /project will display a form to create a new project
# GET /project/<ID> will retrieve the project with the specified ID
# 
# POST /project will create a new project
# POST /project/<ID> will update the existing project with that ID
# ----------------------------------------------------------------------

class InvoiceHandler(Authenticated, BaseHandler):
	pass

