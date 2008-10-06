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
from elections import model
from elections.model import *

import sqlalchemy

from turbogears.database import session

class Admin(controllers.Controller):
    def __init__(self, appTitle):
        self.appTitle = appTitle

    #@expose(template='elections.templates.adminlist')
    @identity.require(identity.in_group("elections"))
    @expose()
    def index(self, **kw):
        return "Hi"
    
    @identity.require(identity.in_group("elections"))
    @expose(template="elections.templates.admnewe")
    def newe(self, **kw):        
        if "submit" in kw:
            if "embargoed" not in kw:
                setembargo=0
            else:
		setembargo=1

            if "allownominations" not in kw:
                setnominations=0
            else:
                setnominations=1
            Elections(alias=kw['alias'], status=0, method=0, shortdesc=kw['shortdesc'], description=kw['info'], url=kw['url'], start_date=kw['startdate'], end_date=kw['enddate'], embargoed=setembargo, seats_elected=kw['seats'], allow_nominations=setnominations, nomination_end=kw['nominationend'])
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
                    Candidates(election_id=kw['id'],name=candidate[0])
                elif len(candidate) == 2:
                    Candidates(election_id=kw['id'],name=candidate[0],formalname=candidate[1])
                elif len(candidate) == 3:
                    if candidate[1] == '':
                        Candidates(election_id=kw['id'],name=candidate[0],url=candidate[2])
                    else:
                        Candidates(election_id=kw['id'],name=candidate[0],formalname=candidate[1],url=candidate[2])
                else:
                    turbogears.flash("There was an issue!")
            raise turbogears.redirect("/admin/newc")
        else:
            return dict()

    #@expose(template="elections.templates.admedit")
    #def edit(self,eid=None):
    #    try:
    #        election = Elections.query.filter_by(id=int(eid)).all()[0]
    #    except ValueError:
    #        election = Elections.query.filter_by(shortname=eid).all()[0]
    #    election = Elections.query.filter_by(id=int(eid)).all()[0]
    #    candidates = Candidates.query.filter_by(election_id=eid).all()
    #    return dict(e=election, candidates=candidates)

    #@expose()
    #def save(self, **kw):
    #    return "Hi"
