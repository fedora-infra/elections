import turbogears
from turbogears import controllers, expose, flash, redirect, config
from turbogears import identity
from turbogears.database import session
from cherrypy import request, response

from fedora.accounts.fas2 import AccountSystem
from elections import model
from elections.model import *
from elections.admin import Admin

import sqlalchemy

from datetime import datetime

class Root(controllers.RootController):
    appTitle = 'Fedora Elections'

    baseURL = config.get('fas.url', 'https://publictest10.fedoraproject.org/accounts/')
    username = config.get('fas.username', 'admin')
    password = config.get('fas.password', 'admin')

    fas = AccountSystem(baseURL, username, password)

    admin = Admin(fas, appTitle)
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
            turbogears.flash("You cannot vote in this election because the end date has passed.  You have been redirected to the election results")
            raise turbogears.redirect("/results/" + str(eid))
        elif election.start_date > curtime:
            election_started=False
        else:
            election_started=True
        candidates = Candidates.query.filter_by(election_id=eid).order_by(Candidates.name).all()
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
        votecount = VoteTally.query.filter_by(election_id=eid).order_by(VoteTally.novotes.desc()).all()
        return dict(votecount=votecount, election=election)


    @expose(template="elections.templates.confirm")
    def vote(self, eid, **kw):   
        election = Elections.query.filter_by(id=eid).all()[0]
        candidates = Candidates.query.filter_by(election_id=eid).order_by(Candidates.name).all()

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

    @expose(template="elections.templates.login", allow_json=True)
    def login(self, forward_url=None, previous_url=None, *args, **kw):
        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
                # User is logged in
                if 'tg_format' in request.params and request.params['tg_format'] == 'json':
                    # When called as a json method, doesn't make any sense to
                    # redirect to a page.  Returning the logged in identity
                    # is better.
                    return dict(user = identity.current.user)
                if not forward_url:
                    forward_url=config.get('base_url_filter.base_url') + '/'
                raise redirect(forward_url)
        
        forward_url=None
        previous_url=request.path

        if identity.was_login_attempted():
            msg="The credentials you supplied were not correct or did not grant access to this resource."
        elif identity.get_identity_errors():
            msg="You must provide your credentials before accessing his resource."
        else:
            msg="Please log in."
            forward_url= request.headers.get("Referer", "/")

        response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=request.params,
                    forward_url=forward_url, title='Fedora Account System Login')

    @expose()
    def logout(self):
        identity.current.logout()
        raise redirect(request.headers.get("Referer","/"))
