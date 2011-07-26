# -*- coding: utf-8 -*-
#
# Copyright © 2008 Nigel Jones, Toshio Kuratomi, Ricky Zhou, Luca Foppiano
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


# Voting functions

#import turbogears
#from turbogears import controllers, expose, flash, redirect, config
#from turbogears import identity
from tg import expose, flash, require, url, request, redirect
from elections2.lib.base import BaseController

from elections2 import model
from elections2.model import Elections, LegalVoters, Candidates, \
    Votes, UserVoteCount

import sqlalchemy

#from turbogears.database import session

from datetime import datetime
import re

class Vote(BaseController):
    allow_only = predicates.not_anonymous()
    
    def __init__(self, fas, appTitle):
        self.fas = fas
        self.appTitle = appTitle

    #TODO: This function will be split off into: default => submit => 
    #confirm functions, hopefully it was simplify everything
    @expose(template="elections2.templates.vote")
    def default(self, eid=None, **kw):
        print dir(Elections)
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
                flash("This election does not exist, check"\
                    " if you have used the correct URL.")
                raise redirect("/")
        except IndexError:
            flash("This election does not exist, check if"\
                    " you have used the correct URL.")
            raise redirect("/")

        request.identity = request.environ.get('repoze.who.identity')
        votergroups = model.DBSession.query(LegalVoters
                                ).filter_by(election_id=eid).all()
        usergroups = request.identity["groups"]
        print usergroups
        print votergroups

        match = 0
        for group in votergroups:
            if group.group_name == "anycla":
                if (len(usergroups) > len([g for g in 
                        usergroups if re.match("cla_.*",g)])
                        ):
                    match = 1
            elif request.identity.in_group(group.group_name) or \
                    group.group_name == "anyany":
                match = 1
        if match == 0:
            flash("You are not in a FAS group that can vote"\
                " in this election, more information can be found at"\
                " the bottom of this page.")
            raise redirect("/about/" + str(eid))
        
        candidates = model.DBSession.query(Candidates
                            ).filter_by(election_id=eid
                            ).order_by(Candidates.name).all()
        uservote = model.DBSession.query(UserVoteCount
                            ).filter_by(election_id=eid,
                    voter=request.identity['username']).all()

        usernamemap = {}

        if election.usefas:
            for c in candidates:
                try:
                    usernamemap[c.id] = self.fas.person_by_username(
                        c.name)['human_name']
                except KeyError:
                    # User has human_name set to private
                    usernamemap[c.id] = c.name

        uvotes = {}
        next_action = ""

        curtime = datetime.utcnow()
        if election.start_date > curtime:
            flash("Voting has not yet started, sorry.")
            raise redirect("/")
        elif election.end_date < curtime:
            flash("You cannot vote in this election because the end date has passed.  You have been redirected to the election results")
            raise redirect("/results/" + election.shortname)
        elif len(uservote) != 0:
            flash("You have already voted in this election!")
            raise redirect("/")
        
        # Lets do this in reverse order
        if "confirm" in kw:
            for c in candidates:
                if str(c.id) in kw:
                    try:
                        range = int(kw[str(c.id)])
                        if range >= 0 and range <= len(candidates):
                            uvotes[c.id] = range
                        else:
                            flash("Invalid Ballot!")
                            raise redirect("/")
                    except ValueError:
                        flash("Invalid Ballot!")
                        raise redirect("/")
            for uvote in uvotes:
                v = Votes()
                v.voter=request.identity['username']
                v.candidate_id=uvote
                v.weight=uvotes[uvote]
                v.election_id=eid
                v.timestamp=curtime
                model.DBSession.add(v)
            flash("Your vote has been recorded, thank you!")
            raise redirect("/")
        elif "vote" in kw:
            flash("Please confirm your vote!")
            for c in candidates:
                if str(c.id) in kw:
                    try:
                        range = int(kw[str(c.id)])
                        if range > len(candidates):
                            flash("Invalid data was detected for one " \
                            "or more candidates and was changed to " \
                            "zeros!  Please correct and resubmit your "\
                            "ballot.")
                            uvotes[c.id] = 0
                            next_action = "vote"
                        elif range >= 0:
                            uvotes[c.id] = range
                        else:
                            flash("Invalid data was " \
                            "detected for one or more candidates and" \
                            "was changed to zeros!  Please correct " \
                            "and resubmit your ballot.")
                            uvotes[c.id] = 0
                            next_action = "vote"
                    except ValueError:
                        flash("Invalid data was detected for one or " \
                        "more candidates and was changed to zeros! " \
                        "Please correct and resubmit your ballot.")
                        uvotes[c.id] = 0
                        next_action = "vote"
                else:
                    flash("Invalid Ballot!")
                    raise redirect("/")
            if next_action != "vote":
                next_action = "confirm"
        else:
            for c in candidates:
                uvotes[c.id] = ""
            next_action = "vote"

        return dict(eid=eid, candidates=candidates, 
                    usernamemap=usernamemap, election=election, 
                    nextaction=next_action, voteinfo=uvotes, 
                    appTitle=self.appTitle)

