import turbogears
from turbogears import controllers, expose, flash, redirect
from elections import model
from elections.model import *

import sqlalchemy

from turbogears.database import session

class Root(controllers.RootController):
    @expose(template="elections.templates.list")
    def index(self):
        electlist = Elections.query.order_by(ElectionsTable.c.start_date).all()
        return dict(elections=electlist)
    @expose(template="elections.templates.info")
    def info(self,eid=None):
        if eid:
            candidates = Candidates.query.filter_by(election_id=eid).all()
            return dict(eid=eid, candidates=candidates)
    @expose()
    def vote(self, cid, **kw):
        '''
        if kw['weight']:
            Votes(voter="fooname",candidate_id=cid,weight=kw['weight'])
            turbogears.flash("Saved!")
            raise turbogears.redirect("/")
        else:
        '''
        Votes(voter="fooname",candidate_id=cid,weight="1")
        turbogears.flash("Saved!")
        raise turbogears.redirect("/")
