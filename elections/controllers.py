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
        return dict(elections=electlist, curtime=datetime.utcnow())


    @expose(template="elections.templates.info")
    def info(self,eid=None):
        try:
            eid = int(eid)
            election = Elections.query.filter_by(id=eid).all()[0]
        except ValueError:
            election = Elections.query.filter_by(shortname=eid).all()[0]
            eid = election.id
        curtime = datetime.utcnow()
        if election.end_date < curtime:
            turbogears.flash("You cannot vote in this election has the end date has passed.  You have been redirected to the election results")
            raise turbogears.redirect("/results/" + str(eid))
        elif election.start_date > curtime:
            election_started=False
        else:
            election_started=True
        candidates = Candidates.query.filter_by(election_id=eid).all()
        return dict(eid=eid, candidates=candidates, election=election, election_started=election_started)

    @expose(template="elections.templates.results")
    def results(self,eid=None):
        try:
            eid = int(eid)
            election = Elections.query.filter_by(id=eid).all()[0]
        except ValueError:
            election = Elections.query.filter_by(shortname=eid).all()[0]
            eid = election.id
        curtime = datetime.utcnow()
        if election.public_results == 0 and election.end_date > curtime:
            turbogears.flash("We are sorry, the results for this election cannot be viewed at this time because the election is still in progress.")
            raise turbogears.redirect("/")
        elif election.start_date > curtime:
            turbogears.flash("We are sorry, the results for this election cannot be viewed at this time because the election has not started.")
            raise turbogears.redirect("/")
        votecount = VoteTally.query.filter_by(election_id=eid).all()
        return dict(votecount=votecount, election=election)


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
                            if range >= 0 and range <= len(candidates):
                                uvotes[c.id] = range
                            else:
                                turbogears.flash("Invalid Ballot!")
                                raise turbogears.redirect("/")
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
                        if range > len(candidates):
                            turbogears.flash("One or more votes had incorrect data, please verify your ballot carefully!")
                            uvotes[c.id] = len(candidates)
                        elif range >= 0:
                            uvotes[c.id] = range
                        else:
                            turbogears.flash("One or more votes had incorrect data, please verify your ballot carefully!")
                            uvotes[c.id] = 0
                    except ValueError:
                        turbogears.flash("Invalid data was detected and changed to zeros!")
                        uvotes[c.id] = 0
                else:
                    turbogears.flash("Invalid Ballot!")
                    raise turbogears.redirect("/")
                      
            return dict(voteinfo=uvotes, candidates=candidates, election=election, voter=kw['name'])
