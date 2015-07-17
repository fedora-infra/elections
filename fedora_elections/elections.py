# -*- coding: utf-8 -*-
#
# Copyright © 2012  Red Hat, Inc.
# Copyright © 2012  Ian Weller <ianweller@fedoraproject.org>
# Copyright © 2012  Toshio Kuratomi <tkuratom@redhat.com>
# Copyright © 2012  Frank Chiulli <fchiulli@fedoraproject.org>
#
# This copyrighted material is made available to anyone wishing to use, modify,
# copy, or redistribute it subject to the terms and conditions of the GNU
# General Public License v.2, or (at your option) any later version.  This
# program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the GNU
# General Public License along with this program; if not, write to the Free
# Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA. Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public License and
# may only be used or replicated with the express permission of Red Hat, Inc.
#
# Author(s):        Ian Weller <ianweller@fedoraproject.org>
#                   Toshio Kuratomi <tkuratom@redhat.com>
#                   Frank Chiulli <fchiulli@fedoraproject.org>
#                   Pierre-Yves Chibon <pingou@fedoraproject.org>
#

from datetime import datetime, time, timedelta
from functools import wraps

import flask
from fedora.client import AuthError

from fedora_elections import fedmsgshim
from fedora_elections import forms
from fedora_elections import models
from fedora_elections import (
    APP, SESSION, FAS2, is_authenticated, is_admin, is_election_admin,
    is_safe_url, safe_redirect_back,
)
from fedora_elections.utils import build_name_map
from sqlalchemy import update

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return flask.redirect(flask.url_for(
                'auth_login', next=flask.request.url))
        elif not flask.g.fas_user.cla_done:
            flask.flash(
                'You must sign the CLA to vote', 'error')
            return safe_redirect_back()
        elif len(flask.g.fas_user.groups) == 0:
            flask.flash(
                'You need to be in one another group than CLA to vote',
                'error')
            return safe_redirect_back()

        return f(*args, **kwargs)
    return decorated_function


def get_valid_election(election_alias, ended=False):
    """ Return the election if it is valid (not pending, not ended).
    """
    election = models.Election.get(SESSION, alias=election_alias)

    if not election:
        flask.flash('The election, %s, does not exist.' % election_alias)
        return safe_redirect_back()

    if election.status == 'Pending':
        flask.flash('Voting has not yet started, sorry.')
        return safe_redirect_back()

    elif not ended and election.status in ('Ended', 'Embargoed'):
        flask.flash(
            'This election is closed.  You have been redirected to the '
            'election results.')
        return flask.redirect(flask.url_for(
            'election_results', election_alias=election.alias))

    elif ended and election.status == 'In progress':
        flask.flash(
            'Sorry but this election is in progress, and you may not see its '
            'results yet.')
        return safe_redirect_back()

    return election


@APP.route('/vote/<election_alias>', methods=['GET', 'POST'])
@login_required
def vote(election_alias):
    election = get_valid_election(election_alias)

    if not isinstance(election, models.Election):
        return election

    if election.legal_voters_list:
        if len(set(flask.g.fas_user.groups).intersection(
                set(election.legal_voters_list))) == 0:
            flask.flash(
                'You are not among the groups that are allowed to vote '
                'for this election', 'error')
            return safe_redirect_back()

    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    revote = True if votes > 0 else False

    if election.voting_type.startswith('range'):
        return vote_range(election, revote)
    elif election.voting_type == 'simple':
        return vote_simple(election)
    elif election.voting_type == 'select':
        return vote_select(election)
    elif election.voting_type == 'irc':
        return vote_irc(election)
    else:  # pragma: no cover
        flask.flash(
            'Unknown election voting type: %s' % election.voting_type)
        return safe_redirect_back()

def vote_range(election, revote):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    num_candidates = election.candidates.count()

    cand_ids = [str(cand.id) for cand in election.candidates]
    next_action = 'confirm'

    max_selection = num_candidates
    if election.max_votes:
        max_selection = election.max_votes

    form = forms.get_range_voting_form(
        candidates=election.candidates,
        max_range=max_selection)

    if form.validate_on_submit():
        if form.action.data == 'submit':
            for candidate in form:
                if candidate.short_name in ['csrf_token', 'action']:
                    continue
                if revote:
                    vote = update(models.Vote).\
                    where(models.Vote.candidate_id == candidate.short_name
                    and models.Vote.voter == flask.g.fas_user.username
                    and models.Vote.election == election.id).\
                    values(value = candidate.data)
                    SESSION.execute(vote)
                    #break out of candidate loop
                    continue

                new_vote = models.Vote(
                    election_id=election.id,
                    voter=flask.g.fas_user.username,
                    timestamp=datetime.now(),
                    candidate_id=candidate.short_name,
                    value=candidate.data,
                )
                SESSION.add(new_vote)
            SESSION.commit()

            flask.flash("Your vote has been recorded.  Thank you!")
            return safe_redirect_back()

        if form.action.data == 'preview':
            flask.flash("Please confirm your vote!")
            next_action = 'vote'

    usernamemap = build_name_map(election)

    return flask.render_template(
        'vote_range.html',
        election=election,
        form=form,
        num_candidates=num_candidates,
        max_range=max_selection,
        usernamemap=usernamemap,
        nextaction=next_action)


def vote_select(election):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    num_candidates = election.candidates.count()

    cand_name = {}
    for candidate in election.candidates:
        cand_name[candidate.name] = candidate.id
    next_action = 'confirm'

    max_selection = num_candidates
    if election.max_votes:
        max_selection = election.max_votes

    form = forms.get_select_voting_form(
        candidates=election.candidates,
        max_selection=max_selection)

    if form.validate_on_submit():

        cnt = 0
        for candidate in form:
            if candidate.short_name in ['csrf_token', 'action']:
                continue
            if candidate.data:
                cnt += 1
        if cnt > max_selection:
            flask.flash('Too many candidates submitted', 'error')
        else:
            if form.action.data == 'submit':
                for candidate in form:
                    if candidate.short_name in ['csrf_token', 'action']:
                        continue

                    new_vote = models.Vote(
                        election_id=election.id,
                        voter=flask.g.fas_user.username,
                        timestamp=datetime.now(),
                        candidate_id=cand_name[candidate.short_name],
                        value=int(candidate.data),
                    )
                    SESSION.add(new_vote)
                SESSION.commit()

                flask.flash("Your vote has been recorded.  Thank you!")
                return safe_redirect_back()

            if form.action.data == 'preview':
                flask.flash("Please confirm your vote!")
                next_action = 'vote'

    usernamemap = build_name_map(election)

    return flask.render_template(
        'vote_simple.html',
        election=election,
        form=form,
        num_candidates=num_candidates,
        max_selection=max_selection,
        usernamemap=usernamemap,
        nextaction=next_action)


def vote_simple(election):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    num_candidates = election.candidates.count()

    next_action = 'confirm'

    form = forms.get_simple_voting_form(
        candidates=election.candidates,
        fasusers=election.candidates_are_fasusers)

    if form.validate_on_submit():
        if form.action.data == 'submit':
            for candidate in form:
                if candidate.short_name in ['csrf_token', 'action']:
                    continue

                new_vote = models.Vote(
                    election_id=election.id,
                    voter=flask.g.fas_user.username,
                    timestamp=datetime.now(),
                    candidate_id=candidate.data,
                    value=1,
                )
                SESSION.add(new_vote)
            SESSION.commit()

            flask.flash("Your vote has been recorded.  Thank you!")
            return safe_redirect_back()

        if form.action.data == 'preview':
            flask.flash("Please confirm your vote!")
            next_action = 'vote'

    return flask.render_template(
        'vote_simple.html',
        election=election,
        form=form,
        num_candidates=num_candidates,
        nextaction=next_action)


def vote_irc(election):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    cand_name = {}
    for candidate in election.candidates:
        cand_name[candidate.name] = candidate.id

    num_candidates = election.candidates.count()

    next_action = 'confirm'
    form = forms.get_irc_voting_form(
        candidates=election.candidates,
        fasusers=election.candidates_are_fasusers)
    if form.validate_on_submit():
        if form.action.data == 'submit':
            for candidate in form:
                if candidate.short_name in ['csrf_token', 'action']:
                    continue
                new_vote = models.Vote(
                    election_id=election.id,
                    voter=flask.g.fas_user.username,
                    timestamp=datetime.now(),
                    candidate_id=cand_name[candidate.short_name],
                    value=candidate.data,
                )
                SESSION.add(new_vote)
            SESSION.commit()
            flask.flash("Your vote has been recorded.  Thank you!")
            return safe_redirect_back()

        if form.action.data == 'preview':
            flask.flash("Please confirm your vote!")
            next_action = 'vote'

    return flask.render_template(
        'vote_simple.html',
        election=election,
        form=form,
        num_candidates=num_candidates,
        nextaction=next_action)


@APP.route('/results/<election_alias>')
def election_results(election_alias):
    election = get_valid_election(election_alias, ended=True)

    if not isinstance(election, models.Election):  # pragma: no cover
        return election

    elif election.embargoed:
        if is_authenticated() and (
                is_admin(flask.g.fas_user)
                or is_election_admin(flask.g.fas_user, election.id)):
            flask.flash("You are only seeing this page because you are "
                        "an admin.", "warning")
            flask.flash("The results for this election are currently "
                        "embargoed pending formal announcement.",
                        "warning")
        else:
            flask.flash("We are sorry.  The results for this election "
                        "cannot be viewed because they are currently "
                        "embargoed pending formal announcement.")
            return safe_redirect_back()

    if is_authenticated() and (
            is_admin(flask.g.fas_user)
            or is_election_admin(flask.g.fas_user, election.id)):
        flask.flash(
            "Check out the <a href='%s'>Text version</a> "
            "to send the annoucement" % flask.url_for(
                'election_results_text', election_alias=election.alias)
            )

    usernamemap = build_name_map(election)

    stats = models.Vote.get_election_stats(SESSION, election.id)

    cnt = 1
    evolution_label = []
    evolution_data = []
    for delta in range((election.end_date - election.start_date).days + 1):
        day = (
            election.start_date + timedelta(days=delta)
        ).strftime('%d-%m-%Y')
        evolution_label.append([cnt, day])
        evolution_data.append([cnt, stats['vote_timestamps'].count(day)])
        cnt += 1

    return flask.render_template(
        'results.html',
        election=election,
        usernamemap=usernamemap,
        stats=stats,
        evolution_label=evolution_label,
        evolution_data=evolution_data,
    )


@APP.route('/results/<election_alias>/text')
def election_results_text(election_alias):
    election = get_valid_election(election_alias, ended=True)

    if not isinstance(election, models.Election):  # pragma: no cover
        return election

    if not (is_authenticated() and (is_admin(flask.g.fas_user)
            or is_election_admin(flask.g.fas_user, election.id))):
        flask.flash(
            "The text results are only available to the admins", "error")
        return safe_redirect_back()

    usernamemap = build_name_map(election)

    stats = models.Vote.get_election_stats(SESSION, election.id)

    return flask.render_template(
        'results_text.html',
        election=election,
        usernamemap=usernamemap,
        stats=stats,
    )
