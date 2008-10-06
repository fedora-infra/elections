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

class Vote(controllers.Controller):
    def __init__(self, appTitle):
        self.appTitle = appTitle

    @identity.require(identity.not_anonymous())
    @expose(template="elections.templates.vote")
    def default(self, eid=None, **kw):
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
	foo = identity.current.groups

        match = 0
        for group in votergroups:
            if group.group_name == "anycla":
                if (len(identity.current.groups) > len([g for g in identity.current.groups if re.match("cla_.*",g)])):
                    match = 1
            elif identity.in_group(group.group_name) or group.group_name == "anyany":
                match = 1
        if match == 0:
            turbogears.flash("You are not in a FAS group that can vote in this election, more information can be found at the bottom of this page.")
            raise turbogears.redirect("/about/" + str(eid))
        
        candidates = Candidates.query.filter_by(election_id=eid).order_by(Candidates.name).all()
        uservote = UserVoteCount.query.filter_by(election_id=eid, voter=turbogears.identity.current.user_name).all()
        uvotes = {}
        next_action = ""

        curtime = datetime.utcnow()
        if election.start_date > curtime:
            turbogears.flash("Voting has not yet started, sorry.")
            raise turbogears.redirect("/")
        elif election.end_date < curtime:
            turbogears.flash("You cannot vote in this election because the end date has passed.  You have been redirected to the election results")
            raise turbogears.redirect("/results/" + election.shortname)
        elif len(uservote) != 0:
            turbogears.flash("You have already voted in this election!")
            raise turbogears.redirect("/")
        
        # Lets do this in reverse order
        if "confirm" in kw:
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
                Votes(voter=turbogears.identity.current.user_name, candidate_id=uvote, weight=uvotes[uvote], election_id=eid, timestamp=curtime)
            turbogears.flash("Your vote has been recorded, thank you!")
            raise turbogears.redirect("/")
        elif "vote" in kw:
            turbogears.flash("Please confirm your vote!")
            for c in candidates:
                if str(c.id) in kw:
                    try:
                        range = int(kw[str(c.id)])
                        if range > len(candidates):
                            turbogears.flash("Invalid data was detected for one or more candidates and was changed to zeros!  Please correct and resubmit your ballot.")
                            uvotes[c.id] = 0
                            next_action = "vote"
                        elif range >= 0:
                            uvotes[c.id] = range
                        else:
                            turbogears.flash("Invalid data was detected for one or more candidates and was changed to zeros!  Please correct and resubmit your ballot.")
                            uvotes[c.id] = 0
                            next_action = "vote"
                    except ValueError:
                        turbogears.flash("Invalid data was detected for one or more candidates and was changed to zeros!  Please correct and resubmit your ballot.")
                        uvotes[c.id] = 0
                        next_action = "vote"
                else:
                    turbogears.flash("Invalid Ballot!")
                    raise turbogears.redirect("/")
            if next_action != "vote":
                next_action = "confirm"
        else:
            for c in candidates:
                uvotes[c.id] = ""
            next_action = "vote"

        return dict(eid=eid, candidates=candidates, election=election, nextaction=next_action, voteinfo=uvotes, appTitle=self.appTitle)

