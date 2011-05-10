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

#import turbogears
#from turbogears import controllers, expose, flash, redirect, config
#from turbogears import identity
from tg import expose, flash, require, url, request, redirect
from elections2.lib.base import BaseController
from fedora.client import AuthError, AppError
from elections2 import model
from elections2.model import Elections, Candidates, \
    LegalVoters, ElectionAdmins

from datetime import datetime

import sqlalchemy, tg

#from turbogears.database import session

identity = request.environ.get('repoze.who.identity')

class Admin(BaseController):
    def __init__(self, fas, appTitle):
        #print dir(fas), fas.username
        self.fas = fas
        self.appTitle = appTitle

    @expose("json")
    def list_elections(self, **kw):
        electlist = model.DBSession.query(Elections).order_by(
                    Elections.start_date).filter('id>0').all()
        elections = [{  'id': e.id, 'alias': e.alias, 
                        'shortdesc': e.shortdesc, 
                        'start_date': e.start_date, 
                        'end_date': e.end_date, 
                        'legal_voters': [
                            {'groupname': lv.group_name} for lv in 
                                model.DBSession.query(LegalVoters
                                    ).filter_by(election_id=e.id)
                                ]} for e in electlist]
        return dict(elections=elections, servertime=datetime.utcnow(), 
                    appTitle=self.appTitle)

    @expose(template='elections2.templates.admin')
    def index(self, *kw, **args):
        print "test"
        electlist = model.DBSession.query(Elections).order_by(
                    Elections.start_date).filter('id>0').all()
        elections = [{'id': e.id, 'alias': e.alias, 
                        'shortdesc': e.shortdesc, 
                        'start_date': e.start_date, 
                        'end_date': e.end_date, 
                        'legal_voters': [
                            {'groupname': lv.group_name} for lv in 
                            model.DBSession.query(LegalVoters
                                    ).filter_by(election_id=e.id)],
                            'embargoed' : e.embargoed}
                            for e in electlist
                    ]
        print "here"
        return dict(elections=elections)
    
    #print "   -> ", request.environ.get("FAS_LOGIN_INFO")
    #@identity.require(identity.in_group("elections"))
    @expose(template="elections2.templates.admnewe")
    def newe(self, **kw):
        print "newe"
        if "submit" in kw:
            print kw
            setembargo=1
            usefas=1
            if "embargoed" not in kw:
                setembargo=0
            if "usefas" not in kw:
                usefas=0
            if kw["seats"] == "":
                flash("The number of seats given is incorrect.")
                return dict()

            election = Elections()
            election.alias=kw['alias'] #status=0, method=0,
            election.shortdesc=kw['shortdesc']
            election.description=kw['info']
            election.url=kw['url']
            election.start_date=kw['startdate']
            election.end_date=kw['enddate']
            election.embargoed=setembargo
            election.seats_elected=kw['seats']
            election.usefas=usefas
            election.votes_per_user=1
            flash("New Election Created")
            print dir(model.DBSession)
            model.DBSession.add(election)
            #model.DBSession.commit()
            print "raise"
            raise redirect("/admin/edit/"+str(election.alias))
        else:
            print "return"
            return dict()

    #@identity.require(identity.in_group("elections"))
    @expose(template="elections2.templates.admnewc")
    def newc(self, **kw):        
        if "submit" in kw:
            for entry in kw['nameurl'].split("|"):
                candidate = entry.split("!")
                #Python doesn't have a good way of doing case/switch statements
                if len(candidate) == 1:
                    Candidates(election_id=kw['id'], name=candidate[0],
                        status=0, human=1)
                elif len(candidate) == 2:
                    Candidates(election_id=kw['id'], name=candidate[0],
                        url=candidate[1], status=0, human=1)
                else:
                    flash("There was an issue!")
            raise redirect("/admin/newc")
        else:
            return dict()

    #@identity.require(identity.in_group("elections"))
    @expose(template="elections2.templates.admedit")
    def edit(self, eid=None, **kw):
        print "**", eid, kw
        if "submit" in kw:
            for entry in kw['newgroups'].split("|"):
                entry.strip()
                if len(entry) :
                    lv = LegalVoters()
                    lv.election_id=kw['id']
                    lv.group_name=entry
                    model.DBSession.add(lv)
            for entry in kw['newadmins'].split("|"):
                entry.strip()
                if len(entry) :
                    ea = ElectionAdmins()
                    ea.election_id=kw['id']
                    ea.group_name=entry
                    model.DBSession.add(ea)
            for key, value in kw.items():
                if key.startswith('remove_'):
                    group = key[len('remove_'):]
                    for lv in model.DBSession.query(LegalVoters).filter_by(
                            election_id=kw['id'],group_name=group) :
                        model.DBSession.delete(lv)
            for key, value in kw.items():
                if key.startswith('removeadmin_'):
                    group = key[len('removeadmin_'):]
                    for admin in model.DBSession.query(ElectionAdmins).filter_by(
                            election_id=kw['id'],group_name=group) :
                        model.DBSession.delete(admin)
            for entry in kw['newcandidates'].split("|"):
                candidate = entry.split("!")
                #Python doesn't have a good way of doing case/switch statements
                if len(candidate) == 1:
                    if len(candidate[0]) : 
                        c=Candidates()
                        c.election_id=kw['id']
                        c.name=candidate[0]
                        c.status=0
                        c.human=1
                        model.DBSession.add(c)
                elif len(candidate) == 2:
                    if len(candidate[0]) : 
                        c = Candidates()
                        c.election_id=kw['id']
                        c.name=candidate[0],
                        c.url=candidate[1]
                        c.status=0
                        c.human=1
                        model.DBSession.add(c)
                else:
                    flash("There was an issue!")
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
                election = model.DBSession.query(Elections).filter_by(
                                                id=int(eid)).all()[0]
            except ValueError:
                election = model.DBSession.query(Elections).filter_by(
                                                alias=eid).all()[0]
            print kw.keys()
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
            model.DBSession.add(election)
            raise redirect("/admin/edit/"+kw['id'])

        try:
            eid = int(eid)
            election = election = model.DBSession.query(Elections
                                ).filter_by(id=eid).all()[0]
        except ValueError:
            try:
                election = election = model.DBSession.query(Elections
                                ).filter_by(alias=eid).all()[0]
                eid = election.id
            except IndexError:
                flash("This election does not exist, check if you have used the correct URL.")
                raise redirect("/admin/")
        except (IndexError, TypeError):
            flash("This election does not exist, check if you have used the correct URL.")
            raise redirect("/admin/")

        if "removeembargo" in kw:
            election.embargoed=0
            flash("Embargo on election results removed")
            raise redirect("/admin/")

        candidates = model.DBSession.query(Candidates
                    ).filter_by(election_id=election.id).all()
        votergroups = model.DBSession.query(LegalVoters
                    ).filter_by(election_id=election.id).all()
        admingroups = model.DBSession.query(ElectionAdmins
                    ).filter_by(election_id=election.id).all()
        groupnamemap = {}
        for g in admingroups:
            try:
                groupnamemap[g.group_name] = g.group_name + " (" 
                + self.fas.group_by_name(g.group_name)['display_name'] +")"
            except (AppError, AuthError, KeyError) :
                groupnamemap[g.group_name] = g.group_name 
        for g in votergroups:
            try:
                groupnamemap[g.group_name] = g.group_name + " (" 
                + self.fas.group_by_name(g.group_name)['display_name'] +")"
            except (AppError, AuthError, KeyError) :
                groupnamemap[g.group_name] = g.group_name 

        return dict(e=election, candidates=candidates,
                    admingroups=admingroups, groups=votergroups,
                    groupnamemap=groupnamemap)
