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
    def __init__(self, fas, appTitle):
        self.fas = fas
        self.appTitle = appTitle

    #@expose(template='elections.templates.adminlist')
    @expose()
    def index(self, **kw):
        return "Hi"
    
    @expose(template="elections.templates.admnew")
    def new(self, **kw):
        #import rpdb2
        #rpdb2.start_embedded_debugger('some_passwd', fAllowUnencrypted = True)
        
        if "submit" in kw:
            if "public_results" not in kw:
                pubresults=0
            else:
                pubresults=1
            Elections(shortname=kw['shortname'],name=kw['name'],info=kw['info'],url=kw['url'],start_date=kw['startdate'],end_date=kw['enddate'],max_seats=int(kw['max_seats']),votes_per_user=1,public_results=pubresults)
            turbogears.redirect("/")
        else:
            return dict()

    #@expose(template="elections.templates.admedit")
    #def edit(self,eid=None):
    #    try:
    #        election = Elections.query.filter_by(id=int(eid)).all()[0]
    #    except ValueError:
    #        election = Elections.query.filter_by(shortname=eid).all()[0]
    #    election = Elections.query.filter_by(id=int(eid)).all()[0]
    #    candidates = Candidates.query.filter_by(election_id=eid).all()
    #    return dict(e=election, candidates=candidates)

    @expose()
    def save(self, **kw):
        return "Hi"
