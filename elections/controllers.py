# -*- coding: utf-8 -*-
#
# Copyright © 2008-2009 Nigel Jones, Toshio Kuratomi, Ricky Zhou, Luca Foppiano All rights reserved.
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2.  This program is distributed in the hope that it
# will be useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.  You should have
# received a copy of the GNU General Public License along with this program;
# if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA. Any Red Hat trademarks that are
# incorporated in the source code or documentation are not subject to the GNU
# General Public License and may only be used or replicated with the express
# permission of Red Hat, Inc.
#
# Author(s): Nigel Jones <nigelj@fedoraproject.org>
#            Toshio Kuratomi <toshio@fedoraproject.org>
#            Ricky Zhou <ricky@fedoraproject.org>
#            Luca Foppiano <lfoppiano@fedoraproject.org>
#
# Report Bugs to https://www.fedorahosted.org/elections

import turbogears
from turbogears import controllers, expose, flash, redirect, config
from turbogears import identity
from turbogears.database import session
from cherrypy import request, response

from fedora.client import AuthError, AppError
from fedora.client.fas2 import AccountSystem
from fedora.tg.controllers import login as fc_login
from fedora.tg.controllers import logout as fc_logout
from elections import model
from elections.model import *
from elections.admin import Admin
from elections.vote import Vote

import sqlalchemy

from datetime import datetime
import re

class Root(controllers.RootController):
    appTitle = 'Fedora Elections'

    baseURL = config.get('fas.url', 'https://admin.fedoraproject.org/accounts/')
    username = config.get('fas.username', 'admin')
    password = config.get('fas.password', 'admin')
    fas = AccountSystem(baseURL, username=username, password=password)

    admin = Admin(fas, appTitle)
    vote = Vote(fas, appTitle)

    @expose(template="elections.templates.index")
    def index(self):
        elections = Elections.query.order_by(ElectionsTable.c.start_date).filter('id>0').all()
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
        return dict(past=past, current=current, future=future, curtime=datetime.utcnow(), appTitle=self.appTitle)

    @expose(template="elections.templates.about")
    def about(self,eid=None):
        try:
            eid = int(eid)
            election = Elections.query.filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = Elections.query.filter_by(alias=eid).all()[0]
                eid = election.id
            except IndexError:
                turbogears.flash("This election does not exist, check if you have used the correct URL.")
                raise turbogears.redirect("/")
        except (IndexError, TypeError):
            turbogears.flash("This election does not exist, check if you have used the correct URL.")
            raise turbogears.redirect("/")

        votergroups = LegalVoters.query.filter_by(election_id=eid).all()
        candidates = Candidates.query.filter_by(election_id=eid).order_by(Candidates.name).all()
        usernamemap = {}
        groupnamemap = {}

        if election.usefas:
            for c in candidates:
                try:
                    usernamemap[c.id] = self.fas.person_by_username(c.name)['human_name']
                except (KeyError, AuthError):
                    # User has their name set to private or user doesn't exist
                    usernamemap[c.id] = c.name
        for g in votergroups:
            try:
                groupnamemap[g.group_name] = g.group_name + " (" + self.fas.group_by_name(g.group_name)['display_name'] +")"
            except (AppError, AuthError, KeyError) :
	        groupnamemap[g.group_name] = g.group_name

        curtime = datetime.utcnow()

        return dict(eid=eid, candidates=candidates, usernamemap=usernamemap, election=election, curtime=curtime, votergroups=votergroups, appTitle=self.appTitle, groupnamemap=groupnamemap)

    @expose(template="elections.templates.results")
    def results(self,eid=None):
        try:
            eid = int(eid)
            election = Elections.query.filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = Elections.query.filter_by(alias=eid).all()[0]
                eid = election.id
            except IndexError:
                turbogears.flash("This election does not exist, check if you have used the correct URL.")
                raise turbogears.redirect("/")
        except (IndexError, TypeError):
            turbogears.flash("This election does not exist, check if you have used the correct URL.")
            raise turbogears.redirect("/")

        usernamemap = {}

        if election.usefas:
            for c in election.candidates:
                try:
                    usernamemap[c.id] = self.fas.person_by_username(c.name)['human_name']
                except (AuthError, KeyError) :
                    # User has their name set to private
                    usernamemap[c.id] = c.name

        curtime = datetime.utcnow()
        if election.end_date > curtime:
            turbogears.flash("We are sorry, the results for this election cannot be viewed at this time because the election is still in progress.")
            raise turbogears.redirect("/")
        elif election.start_date > curtime:
            turbogears.flash("We are sorry, the results for this election cannot be viewed at this time because the election has not started.")
            raise turbogears.redirect("/")
        elif election.embargoed == 1:
            turbogears.flash("We are sorry, the results for this election cannot be viewed because they are currently embargoed pending formal announcement.")
            raise turbogears.redirect("/")
        votecount = VoteTally.query.filter_by(election_id=eid).order_by(VoteTally.novotes.desc()).all()
        return dict(votecount=votecount, usernamemap=usernamemap, election=election, appTitle=self.appTitle)

    @identity.require(identity.not_anonymous())
    @expose(template="elections.templates.verify")
    def verify(self):
        validvotes = {}
	invalidvotes = {}
        c = 0
        allvotes = UserVoteCount.query.filter_by(voter=turbogears.identity.current.user_name).all()
        for v in allvotes:
            if len(v.election.candidates) == v.novotes:
                validvotes[c] = v
                c=c+1
            else:
                invalidvotes[c] = v
                c=c+1
        return dict(validvotes=validvotes, invalidvotes=invalidvotes, appTitle=self.appTitle)
            

    @expose(template="elections.templates.login", allow_json=True)
    def login(self, forward_url=None, *args, **kwargs):
        login_dict = fc_login(forward_url, args, kwargs)
        login_dict['appTitle'] = '%s -- Fedora Account System Login' % \
                self.appTitle
        return login_dict

    @expose(allow_json=True)
    def logout(self):
        return fc_logout()
