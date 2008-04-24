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
        if "weight" in kw and "name" in kw:
            eid = Candidates.query.filter_by(id=cid).all()[0].election_id
            uservote = UserVoteCount.query.filter_by(election_id=eid, voter=kw['name']).all()
            voteperuser = Elections.query.filter_by(id=eid).all()[0].votes_per_user
            if len(uservote) == 0 or uservote < voteperuser: 
                Votes(voter=kw['name'],candidate_id=cid,weight=kw['weight'],election_id=eid)
                turbogears.flash("Saved!")
                raise turbogears.redirect("/")
            else:
                turbogears.flash("You've voted too many times!")
                raise turbogears.redirect("/")
        else:
            turbogears.flash("Wacko!")
            raise turbogears.redirect("/")
