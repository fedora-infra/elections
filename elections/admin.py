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


# Admin functions go here (i.e. add/delete elections)

import turbogears
from turbogears import controllers, expose, flash, redirect, config
from turbogears import identity
from fedora.client import AuthError, AppError
from elections import model
from elections.model import Elections, ElectionsTable, Candidates, LegalVoters

from datetime import datetime

import sqlalchemy

from turbogears.database import session

class Admin(controllers.Controller):
    def __init__(self, fas, appTitle):
        self.fas = fas
        self.appTitle = appTitle

    @expose(allow_json=True)
    def list_elections(self, **kw):
        electlist = Elections.query.order_by(ElectionsTable.c.start_date).filter('id>0').all()
        elections = [{'id': e.id, 'alias': e.alias, 'shortdesc': e.shortdesc, 'start_date': e.start_date, 'end_date': e.end_date, 'legal_voters': [{'groupname': lv.group_name} for lv in LegalVoters.query.filter_by(election_id=e.id)]} for e in electlist]
        return dict(elections=elections, servertime=datetime.utcnow(), appTitle=self.appTitle)

    @expose(template='elections.templates.admin')
    @identity.require(identity.in_group("elections"))
    def index(self, **kw):
        electlist = Elections.query.order_by(ElectionsTable.c.start_date).filter('id>0').all()
        elections = [{'id': e.id, 'alias': e.alias, 'shortdesc': e.shortdesc, 'start_date': e.start_date, 'end_date': e.end_date, 'legal_voters': [{'groupname': lv.group_name} for lv in LegalVoters.query.filter_by(election_id=e.id)], 'embargoed' : e.embargoed} for e in electlist]
        return dict(elections=elections)
    
    @identity.require(identity.in_group("elections"))
    @expose(template="elections.templates.admnewe")
    def newe(self, **kw):        
        if "submit" in kw:
            setembargo=1
            usefas=1
            if "embargoed" not in kw:
                setembargo=0
            if "usefas" not in kw:
                usefas=0

            Elections(alias=kw['alias'], status=0, method=0, shortdesc=kw['shortdesc'], description=kw['info'], url=kw['url'], start_date=kw['startdate'], end_date=kw['enddate'], embargoed=setembargo, seats_elected=kw['seats'],usefas=usefas,votes_per_user=1)
            raise turbogears.redirect("/")
        else:
            return dict()

    @identity.require(identity.in_group("elections"))
    @expose(template="elections.templates.admnewc")
    def newc(self, **kw):        
        if "submit" in kw:
            for entry in kw['nameurl'].split("|"):
                candidate = entry.split("!")
                #Python doesn't have a good way of doing case/switch statements
                if len(candidate) == 1:
                    Candidates(election_id=kw['id'],name=candidate[0], status=0, human=1)
                elif len(candidate) == 2:
                    Candidates(election_id=kw['id'],name=candidate[0],url=candidate[1], status=0, human=1)
                else:
                    turbogears.flash("There was an issue!")
            raise turbogears.redirect("/admin/newc")
        else:
            return dict()

    @identity.require(identity.in_group("elections"))
    @expose(template="elections.templates.admedit")
    def edit(self, eid=None, **kw):
        if "submit" in kw:
            for entry in kw['newgroups'].split("|"):
                entry.strip()
		if len(entry) :
                    LegalVoters(election_id=kw['id'], group_name=entry)
            for key, value in kw.items():
                if key.startswith('remove_'):
                    group = key[len('remove_'):]
                    for lv in LegalVoters.query.filter_by(election_id=kw['id'],group_name=group) :
                        session.delete(lv)
            setembargo=1
            usefas=1
            nominations=1
            if "embargoed" not in kw:
                setembargo=0
            if "usefas" not in kw:
                usefas=0
            if "allownominations" not in kw:
                nominations=0
            try:
                election = Elections.query.filter_by(id=int(eid)).all()[0]
            except ValueError:
                election = Elections.query.filter_by(alias=eid).all()[0]
            election.alias=kw['alias']
            election.status=0
            election.method=0
            election.shortdesc=kw['shortdesc']
            election.description=kw['info']
            election.url=kw['url']
            election.start_date=kw['startdate']
            election.end_date=kw['enddate']
            election.embargoed=setembargo
            election.seats_elected=kw['seats']
            election.usefas=usefas
            election.votes_per_user=kw['votes']
            election.allow_nominations=nominations
            raise turbogears.redirect("/admin/edit/"+kw['id'])

        try:
            eid = int(eid)
            election = Elections.query.filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = Elections.query.filter_by(alias=eid).all()[0]
                eid = election.id
            except IndexError:
                turbogears.flash("This election does not exist, check if you have used the correct URL.")
                raise turbogears.redirect("/admin/")
        except (IndexError, TypeError):
            turbogears.flash("This election does not exist, check if you have used the correct URL.")
            raise turbogears.redirect("/admin/")

        if "removeembargo" in kw:
            election.embargoed=0
            turbogears.flash("Embargo on election results removed")
            raise turbogears.redirect("/admin/")

        candidates = Candidates.query.filter_by(election_id=election.id).all()
	votergroups = LegalVoters.query.filter_by(election_id=election.id).all()
        groupnamemap = {}
        for g in votergroups:
            try:
                groupnamemap[g.group_name] = g.group_name + " (" + self.fas.group_by_name(g.group_name)['display_name'] +")"
            except (AppError, AuthError, KeyError) :
                groupnamemap[g.group_name] = g.group_name 

        return dict(e=election, candidates=candidates, groups=votergroups, groupnamemap=groupnamemap)
