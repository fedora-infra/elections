# -*- coding: utf-8 -*-
#
# Copyright © 2008 Nigel Jones, Toshio Kuratomi, Ricky Zhou, Luca Foppiano All rights reserved.
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

from fedora.client.fas2 import AccountSystem
from elections import model
from elections.model import *
from elections.admin import Admin
from elections.vote import Vote

import sqlalchemy

from datetime import datetime
import re

class Root(controllers.RootController):
    appTitle = 'Fedora Elections'

    admin = Admin(appTitle)
    vote = Vote(appTitle)


    @expose(template="elections.templates.index")
    def index(self):
        electlist = Elections.query.order_by(ElectionsTable.c.start_date).filter('id>0').all()
        return dict(elections=electlist, curtime=datetime.utcnow(), appTitle=self.appTitle)

    @expose(template="elections.templates.about")
    def about(self,eid=None):
        try:
            eid = int(eid)
            election = Elections.query.filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = Elections.query.filter_by(shortname=eid).all()[0]
                eid = election.id
            except IndexError:
                turbogears.flash("This election does not exist, check if you have used the correct URL.")
                raise turbogears.redirect("/")
        except IndexError:
            turbogears.flash("This election does not exist, check if you have used the correct URL.")
            raise turbogears.redirect("/")

        votergroups = LegalVoters.query.filter_by(election_id=eid).all()
        candidates = Candidates.query.filter_by(election_id=eid).order_by(Candidates.name).all()

        curtime = datetime.utcnow()

        return dict(eid=eid, candidates=candidates, election=election, curtime=curtime, votergroups=votergroups, appTitle=self.appTitle)

    @expose(template="elections.templates.results")
    def results(self,eid=None):
        try:
            eid = int(eid)
            election = Elections.query.filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = Elections.query.filter_by(shortname=eid).all()[0]
                eid = election.id
            except IndexError:
                turbogears.flash("This election does not exist, check if you have used the correct URL.")
                raise turbogears.redirect("/")
        except IndexError:
            turbogears.flash("This election does not exist, check if you have used the correct URL.")
            raise turbogears.redirect("/")

        curtime = datetime.utcnow()
        if election.public_results == 0 and election.end_date > curtime:
            turbogears.flash("We are sorry, the results for this election cannot be viewed at this time because the election is still in progress.")
            raise turbogears.redirect("/")
        elif election.start_date > curtime:
            turbogears.flash("We are sorry, the results for this election cannot be viewed at this time because the election has not started.")
            raise turbogears.redirect("/")
        elif election.public_results == 0 and election.embargoed == 1:
            turbogears.flash("We are sorry, the results for this election cannot be viewed because they are currently embargoed pending formal announcement.")
            raise turbogears.redirect("/")
        votecount = VoteTally.query.filter_by(election_id=eid).order_by(VoteTally.novotes.desc()).all()
        return dict(votecount=votecount, election=election, appTitle=self.appTitle)

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
            msg="You must provide your credentials before accessing this resource."
        else:
            msg="Please log in."
            forward_url= request.headers.get("Referer", "/")

        response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=request.params,
                    forward_url=forward_url, appTitle=self.appTitle + ' -- Fedora Account System Login')

    @expose()
    def logout(self):
        identity.current.logout()
        raise redirect(request.headers.get("Referer","/"))
