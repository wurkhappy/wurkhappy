import re

from base import *
from models.user import User
from models.project import Project
from models.invoice import Invoice
from models.lineitem import LineItem
from controllers.verification import Verification

# ----------------------------------------------------------------------
# Invoice Handler
#
# GET /invoice will display a form to create a new invoice
# GET /invoice/<ID> will retrieve the invoice with the specified ID
# 
# POST /invoice will create a new invoice
# POST /invoice/<ID> will update the existing invoice with that ID
# ----------------------------------------------------------------------

class InvoiceHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def get(self, invoiceID=None):
		user = self.current_user
		
		kwargs = {
			'logged_in_user': user
		}
		
		if invoiceID:
			invoice = Invoice.retrieveByID(invoiceID)
			
			if not invoice:
				self.set_status(404)
				self.write("Project not found")
				return
			
			if user.id != invoice.userID or user.id != invoice.clientID:
				self.set_status(403)
				self.write("Forbidden")
				return
			
			project = Project.retrieveByID(invoice.projectID)
			client = User.retrieveByID(invoice.clientID)
			lineItems = LineItem.iteratorWithInvoiceID(invoiceID)
			
			title = "%s: Invoice to %s %s on %s" % (project.name, client.firstName, client.lastName, invoice.dateSent)
			kwargs['title'] = title
			kwargs['invoice'] = invoice
			kwargs['project'] = project
			kwargs['client'] = client
			kwargs['lineItems'] = lineItems
			
			if self.get_argument('edit', False):
				if user.id != invoice.userID:
					self.set_status(403)
					self.write("Forbidden")
					return
					
				self.render('invoice/edit.html', **kwargs)
			else:
				self.render('invoice/show.html', **kwargs)
		else:
			projectID = self.get_argument('projectID', None)
			
			project = Project.retrieveByID(projectID)
			
			if not project:
				self.set_status(404)
				self.write("Project not found")
				return
			
			if user.id != project.userID:
				self.set_status(403)
				self.write("Forbidden")
				return
			
			
			kwargs['title'] = "New Invoice"
			kwargs['user'] = user
			self.render('invoice/edit.html', **kwargs)
		
	@web.authenticated
	def post(self, invoiceID=None):
		pass
		
class LineItemHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def post(self):
		user = self.current_user
		
		invoiceID = self.get_argument('invoice_id', None)
		
		invoice = Invoice.retrieveByID(invoiceID)
		
		if not invoice or user.id != invoice.userID:
			self.set_status(400)
			self.write("Invalid Invoice ID")
			return
		
		lineItem = LineItem()
		lineItem.invoiceID = invoice.id
		lineItem.name = self.get_argument('name', None)
		lineItem.price = self.get_argument('price', None)
		
		lineItem.save()
		
		self.set_status(201)
		self.renderJSON(lineItem.getPublicDictionary())
		return
	
	@web.authenticated
	def delete(self, lineItemID):
		user = self.current_user
		
		lineItem = LineItem.retrieveByID(lineItemID)
		
		#if not lineItem or user.id
		