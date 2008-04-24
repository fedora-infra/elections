# Admin functions go here (i.e. add/delete elections)

import turbogears
from turbogears import controllers, expose, flash, redirect
from elections import model
from elections.model import *

import sqlalchemy

from turbogears.database import session

# All instances of CHANGEME need to be changed to ensure that a user is in an admin group when we start authing against FAS
CHANGEME=1

class Admin(controllers.Controller):
    #@expose(template='elections.templates.adminlist')
    @expose()
    def index(self, **kw):
        return "Hi"
    #@expose(template='elections.templates.adminedit')
    @expose()
    def edit(self, **kw):
        if eid in kw:
            # Editing an Election
            return "Hi"
        else:
            # New Election
            return "Hi"
    @expose()
    def save(self, **kw):
        return "Hi"
