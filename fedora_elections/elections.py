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

from datetime import datetime
from functools import wraps

import flask

from fedora_elections import forms
from fedora_elections import models
from fedora_elections import (
    OIDC, APP, SESSION, is_authenticated, is_admin, is_election_admin,
    safe_redirect_back,
)
from fedora_elections.utils import build_name_map


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
        else:
            user_groups = OIDC.user_getfield('groups')
            if len(user_groups) == 0:
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
        return flask.redirect(flask.url_for(
            'about_election', election_alias=election.alias))

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
        user_groups = OIDC.user_getfield('groups')
        if len(set(user_groups).intersection(
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
        return vote_simple(election, revote)
    elif election.voting_type == 'select':
        return vote_select(election, revote)
    elif election.voting_type == 'irc':
        return vote_irc(election, revote)
    else:  # pragma: no cover
        flask.flash(
            'Unknown election voting type: %s' % election.voting_type)
        return safe_redirect_back()


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
        candidates=sorted(
            election.candidates, key=lambda x: x.vote_count, reverse=True)
    )


def vote_range(election, revote):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id)

    num_candidates = election.candidates.count()
    next_action = 'confirm'

    max_selection = num_candidates
    if election.max_votes:
        max_selection = election.max_votes

    form = forms.get_range_voting_form(
        candidates=election.candidates,
        max_range=max_selection)

    if form.validate_on_submit():
        if form.action.data == 'submit':
            candidates = [
                candidate
                for candidate in form
                if candidate
                and candidate.short_name not in ['csrf_token', 'action']
            ]
            process_vote(candidates, election, votes, revote)
            say_thank_you(election)
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


def vote_select(election, revote):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id)

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
        cnt = [
            candidate
            for candidate in form
            if candidate.data
            and candidate.short_name not in ['csrf_token', 'action']
        ]
        if len(cnt) > max_selection:
            flask.flash('Too many candidates submitted', 'error')
        else:
            if form.action.data == 'submit':
                candidates = [
                    candidate
                    for candidate in form
                    if candidate
                    and candidate.short_name not in ['csrf_token', 'action']
                ]
                process_vote(candidates, election, votes, revote, cand_name)
                say_thank_you(election)
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


def vote_simple(election, revote):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id)

    num_candidates = election.candidates.count()

    next_action = 'confirm'

    form = forms.get_simple_voting_form(
        candidates=election.candidates,
        fasusers=election.candidates_are_fasusers)

    if form.validate_on_submit():
        if form.action.data == 'submit':
            candidates = [
                candidate
                for candidate in form
                if candidate
                and candidate.short_name not in ['csrf_token', 'action']
            ]
            process_vote(candidates, election, votes, revote, value=1)
            say_thank_you(election)
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


def vote_irc(election, revote):
    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id)

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
            candidates = [
                candidate
                for candidate in form
                if candidate
                and candidate.short_name not in ['csrf_token', 'action']
            ]
            process_vote(candidates, election, votes, revote, cand_name)
            say_thank_you(election)
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


def process_vote(
        candidates, election, votes, revote, cand_name=None, value=None):
    for index in range(len(candidates)):
        candidate = candidates[index]
        if revote and (index+1 <= len(votes)):
            vote = votes[index]
            if value is not None:
                vote.candidate_id = candidate.data
            else:
                vote.value = value if value else int(candidate.data)
            SESSION.add(vote)
        else:
            if value is not None:
                cand_id = candidate.data
            elif cand_name:
                cand_id = cand_name[candidate.short_name]
            else:
                cand_id = candidate.short_name

            new_vote = models.Vote(
                election_id=election.id,
                voter=flask.g.fas_user.username,
                timestamp=datetime.utcnow(),
                candidate_id=cand_id,
                value=value if value else int(candidate.data),
            )
            SESSION.add(new_vote)
        SESSION.commit()


def say_thank_you(election):
    thank_you = "Your vote has been recorded.  Thank you!"
    if election.url_badge:
        thank_you = thank_you + '<br><a href="' + \
            election.url_badge + '" target=_new>Claim your I Voted badge</a>.'
    flask.flash(thank_you)
