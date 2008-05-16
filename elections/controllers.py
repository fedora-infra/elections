import turbogears
from turbogears import controllers, expose, flash, redirect
from elections import model
from elections.model import *
from elections.admin import Admin

import sqlalchemy

from turbogears.database import session

from datetime import datetime

class Root(controllers.RootController):
    admin = Admin()
    @expose(template="elections.templates.list")
    def index(self):
        electlist = Elections.query.order_by(ElectionsTable.c.start_date).filter('id>0').all()
        return dict(elections=electlist, currenttime=datetime.utcnow())


    @expose(template="elections.templates.info")
    def info(self,eid=None):
        try:
            eid = int(eid)
        except ValueError:
            eid = Elections.query.filter_by(shortname=eid).all()[0].id
        candidates = Candidates.query.filter_by(election_id=eid).all()
        return dict(eid=eid, candidates=candidates)


    @expose(template="elections.templates.confirm")
    def vote(self, eid, **kw):   
        #import rpdb2
        #rpdb2.start_embedded_debugger('some_passwd', fAllowUnencrypted = True)
        election = Elections.query.filter_by(id=eid).all()[0]
        candidates = Candidates.query.filter_by(election_id=eid).all()

        #Before we do *ANYTHING* check if voting hasn't begun/has ended
        curtime = datetime.utcnow()
        if election.start_date > curtime:
            turbogears.flash("Voting has not yet begun.")
            raise turbogears.redirect("/")
        elif election.end_date < curtime:
            turbogears.flash("We are sorry, voting has now ended.")
            raise turbogears.redirect("/")

        if "confirm" in kw:
            #eid = Candidates.query.filter_by(id=cid).all()[0].election_id
            uservote = UserVoteCount.query.filter_by(election_id=eid, voter=kw['name']).all()
            voteperuser = Elections.query.filter_by(id=eid).all()[0].votes_per_user
            if len(uservote) == 0: 
                uvotes = {}
                for c in candidates:
                    if str(c.id) in kw:
                        try:
                            range = int(kw[str(c.id)])
                            uvotes[c.id] = range
                        except ValueError:
                            turbogears.flash("Invalid Ballot!")
                            raise turbogears.redirect("/")
                for uvote in uvotes:
                    Votes(voter=kw['name'],candidate_id=uvote,weight=uvotes[uvote],election_id=eid)
                turbogears.flash("Saved!")
                raise turbogears.redirect("/")
            else:
                turbogears.flash("You've voted too many times!")
                raise turbogears.redirect("/")
        else:
            turbogears.flash("Please confirm your vote!")
            uvotes = {}
            for c in candidates:
                if str(c.id) in kw:
                    try:
                        range = int(kw[str(c.id)])
                        uvotes[c.id] = range
                    except ValueError:
                        turbogears.flash("Invalid Ballot!")
                        raise turbogears.redirect("/")
                else:
                    turbogears.flash("Invalid Ballot!")
                    raise turbogears.redirect("/")
                      
            return dict(voteinfo=uvotes, candidates=candidates, election=election, voter=kw['name'])
