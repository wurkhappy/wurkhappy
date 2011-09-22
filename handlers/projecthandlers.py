import re

from base import *
from models.user import User
from models.project import Project
from helpers.verification import Verification
from helpers.validation import Validation


# ----------------------------------------------------------------------
# Project Handler
#
# GET /project will display a form to create a new project
# GET /project/<ID> will retrieve the project with the specified ID
# 
# POST /project will create a new project
# POST /project/<ID> will update the existing project with that ID
# ----------------------------------------------------------------------

class ProjectHandler(Authenticated, BaseHandler):
	
	@web.authenticated
	def get(self, projectID=None):
		user = self.current_user
		
		if not user:
			self.set_status(403)
			self.write("Forbidden")
			return
		
		if projectID:
			project = Project.retrieveByID(projectID)
			
			if not project:
				self.set_status(404)
				self.write("Project not found")
				return
			
			invoices = Invoice.iteratorWithProjectID(projectID)
			client = User.retrieveByID(project.clientID)
			
			if self.get_argument('edit', False):
				self.render('project/edit.html', title=project.name, user=user, project=project, client=client, invoices=invoices, logged_in_user=user)
			else:
				self.render('project/show.html', title=project.name, user=user, project=project, client=client, invoices=invoices, logged_in_user=user)
		else:
			self.render('project/edit.html', title="New Project", user=user, project=None, client=None, invoices=[], logged_in_user=user)
	
	@web.authenticated
	def post(self, projectID=None):
		user = self.current_user
		
		if projectID:
			project = Project.retrieveByID(projectID)
			
			if not project:
				self.set_status(404)
				self.write("Project not found")
				return
			
			project.clientID = self.get_argument('client_id')
			project.name = self.get_argument('name')
			project.save()
			
			invoices = Invoice.iteratorWithProjectID(projectID)
			client = User.retrieveByID(project.clientID)
			
			self.set_status(200)
		else:
			project = Project()
			
			if not project:
				self.set_status(404)
				self.write("Project not found")
				return
			
			project.userID = user.id
			project.clientID = self.get_argument('client_id')
			project.name = self.get_argument('name')
			project.save()
			
			invoices = []
			
			client = User.retrieveByID(project.clientID)
			
			self.set_status(201)
			self.set_header('Location', 'http://' + self.request.host + '/project/' + str(project.id))
			return
		self.render('project/show.html', title=project.name, user=user, project=project,  client=client, invoices=invoices, logged_in_user=user)
	
