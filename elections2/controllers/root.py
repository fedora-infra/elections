# -*- coding: utf-8 -*-
"""Main Controller"""

from tg import expose, flash, require, url, request, redirect
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tgext.admin.tgadminconfig import TGAdminConfig
from tgext.admin.controller import AdminController
from repoze.what import predicates

from elections2.lib.base import BaseController
from elections2.model import DBSession, metadata
from elections2.controllers.error import ErrorController
from elections2 import model
from elections2.controllers.secure import SecureController

from fedora.client import AuthError, AppError
from fedora.client.fas2 import AccountSystem

from elections2 import model
from elections2.model import *
from elections2.lib.admin import Admin
from elections2.lib.vote import Vote


from datetime import datetime

__all__ = ['RootController']


class RootController(BaseController):
    """
    The root controller for the elections2 application.

    All the other controllers and WSGI applications should be mounted on this
    controller. For example::

        panel = ControlPanelController()
        another_app = AnotherWSGIApplication()

    Keep in mind that WSGI applications shouldn't be mounted directly: They
    must be wrapped around with :class:`tg.controllers.WSGIAppController`.

    """
    secc = SecureController()

    admin = AdminController(model, DBSession, config_type=TGAdminConfig)

    error = ErrorController()
    
    appTitle = 'Fedora Elections'

    baseURL = "https://admin.fedoraproject.org/accounts"
    username = "elections"
    password = "elections2"
    fas = AccountSystem(baseURL, username=username, password=password)

    admin = Admin(fas, appTitle)
    vote = Vote(fas, appTitle)

    request.identity = request.environ.get('repoze.who.identity')

    @expose('elections2.templates.index')
    def index(self):
        """Handle the front-page."""
        if request.identity:
            userid = request.identity['repoze.who.userid']
            flash(_('Welcome back, %s!') % userid)
        
        elections = model.DBSession.query(Elections).order_by(
                        Elections.start_date).filter('id>0').all()
        past = []
        current = []
        future = []
        now = datetime.utcnow()
        for e in elections:
            if e.start_date > now :
                future.append(e)
            elif e.end_date < now :
                past.append(e)
            else :
                current.append(e)               
        return dict(past=past, current=current, future=future, 
                    curtime=datetime.utcnow(), appTitle=self.appTitle)

    @expose('elections2.templates.about')
    def about(self, eid=None):
        """Handle the 'about' page."""
        try:
            eid = int(eid)
            election = model.DBSession.query(Elections
                            ).filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = model.DBSession.query(Elections
                            ).filter_by(alias=eid).all()[0]
                eid = election.id
            except IndexError:
                flash("This election does not exist, check" \
                        " if you have used the correct URL.")
                raise redirect("/")
        except (IndexError, TypeError):
            flash("This election does not exist, check if" \
                        " you have used the correct URL.")
            raise redirect("/")

        candidates = model.DBSession.query(Candidates
                    ).filter_by(election_id=election.id).all()
        votergroups = model.DBSession.query(LegalVoters
                    ).filter_by(election_id=election.id).all()
        usernamemap = {}
        groupnamemap = {}

        if election.usefas:
            for c in candidates:
                try:
                    usernamemap[c.id] = \
                        self.fas.person_by_username(c.name)['human_name']
                except (KeyError, AuthError):
                    # User has their name set to private or user doesn't exist
                    usernamemap[c.id] = c.name
        for g in votergroups:
            try:
                groupnamemap[g.group_name] = g.group_name + " (" + \
                    self.fas.group_by_name(g.group_name)['display_name'] +")"
            except (AppError, AuthError, KeyError) :
                groupnamemap[g.group_name] = g.group_name

        curtime = datetime.utcnow()

        return dict(eid=eid, candidates=candidates,
                    usernamemap=usernamemap, election=election,
                    curtime=curtime, votergroups=votergroups,
                    appTitle=self.appTitle, groupnamemap=groupnamemap)

    @expose(template="elections2.templates.verify")
    @require(predicates.not_anonymous("Please log-in"))
    def verify(self):
        validvotes = {}
        invalidvotes = {}
        c = 0
        allvotes = UserVoteCount.query.filter_by(voter=
                        turbogears.identity.current.user_name).all()
        for v in allvotes:
            if len(v.election.candidates) == v.novotes:
                validvotes[c] = v
                c=c+1
            else:
                invalidvotes[c] = v
                c=c+1
        return dict(validvotes=validvotes, invalidvotes=invalidvotes,
                    appTitle=self.appTitle)

    #@expose(allow_json=True)
    @expose()
    def logout(self):
        return fc_logout()

    @expose('elections2.templates.login')
    def login(self, came_from=url('/'), csrf_login = None):
        """Start the user login."""
        # code from elections v1
        #login_dict = fc_login(forward_url, args, kwargs)
        login_dict = {}
        login_dict['appTitle'] = '%s -- Fedora Account System Login' % \
                self.appTitle
        login_dict['message'] = _("Please log-in")
        login_dict['previous_url'] = came_from
        login_dict['forward_url'] = "/post_login"
        login_dict['original_parameters'] = request.params

        login_counter = request.environ['repoze.who.logins']
        if login_counter > 0:
            flash(_('Wrong credentials'), 'warning')
        if login_counter > 5:
            flash(_('Too many wrong attempts -- Blocked user'), 'warning')
        login_dict['login_counter'] = str(login_counter)
        login_dict['page'] = 'login'
        login_dict['came_from'] = came_from
        print csrf_login

        return login_dict

        ## Default code from TG2
        #login_counter = request.environ['repoze.who.logins']
        #return dict(page='login', login_counter=str(login_counter),
                    #came_from=came_from)

    @expose(template="elections2.templates.results")
    def results(self, eid=None):
        try:
            eid = int(eid)
            election = model.DBSession.query(Elections).filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = model.DBSession.query(Elections).filter_by(alias=eid).all()[0]
                eid = election.id
            except IndexError:
                flash("This election does not exist, check"\
                        " if you have used the correct URL.")
                raise redirect("/")
        except (IndexError, TypeError):
            flash("This election does not exist, check if"\
                    " you have used the correct URL.")
            raise redirect("/")

        usernamemap = {}

        if election.usefas:
            for c in election.candidates:
                try:
                    usernamemap[c.id] = self.fas.person_by_username(
                            c.name)['human_name']
                except (AuthError, KeyError) :
                    # User has their name set to private
                    usernamemap[c.id] = c.name

        curtime = datetime.utcnow()
        if election.end_date > curtime:
            turbogears.flash("We are sorry, the results for this"\
                " election cannot be viewed at this time because the"\
                " election is still in progress.")
            raise turbogears.redirect("/")
        elif election.start_date > curtime:
            turbogears.flash("We are sorry, the results for this election cannot be viewed at this time because the election has not started.")
            raise turbogears.redirect("/")
        elif election.embargoed == 1:
            if identity.in_group('elections') :
                pass
            else :
                match = 0
                admingroups = model.DBSession.query(ElectionAdmins).filter_by(
                            election_id=eid).all()
                for group in admingroups:
                    if identity.in_group(group.group_name):
                        match = 1
                if match == 0:
                    turbogears.flash("Meep, We are sorry, the results"\
                    " for this election cannot be viewed because they"\
                    " are currently embargoed pending formal"
                    " announcement.")
                    raise turbogears.redirect("/")
        votecount = model.DBSession.query(VoteTally).filter_by(election_id=eid
                            ).order_by(VoteTally.novotes.desc()).all()
        return dict(votecount=votecount, usernamemap=usernamemap,
                    election=election, appTitle=self.appTitle)

    @expose()
    def post_login(self, came_from='/', *args, **kwargs):
        """
        Redirect the user to the initially requested page on successful
        authentication or redirect her back to the login page if login failed.

        """
        ## default code from TG2:
        print request.identity
        if not request.identity:
            login_counter = request.environ['repoze.who.logins'] + 1
            redirect('/login', came_from=came_from, __logins=login_counter)
        userid = request.identity['repoze.who.userid']
        print request.identity.keys()
        flash(_('Welcome back, %s!') % userid)
        redirect(came_from)

    @expose()
    def post_logout(self, came_from='/'):
        """
        Redirect the user to the initially requested page on logout and say
        goodbye as well.

        """
        flash(_('We hope to see you soon!'))
        redirect(came_from)
