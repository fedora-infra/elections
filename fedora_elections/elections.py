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

from datetime import datetime, time
from functools import wraps

import flask
from sqlalchemy.orm.exc import NoResultFound

from fedora_elections import fedmsgshim
from fedora_elections import forms
from fedora_elections import models
from fedora_elections import (
    APP, SESSION, is_authenticated, is_admin, is_safe_url,
    safe_redirect_back,
)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return flask.redirect(flask.url_for(
                'auth_login', next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


def get_valid_election(election_alias, ended=False):
    """ Return the election if it is valid (no pending, not ended).
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
            'Sorry but this election is in progress, you may not see its '
            'results already.')
        return safe_redirect_back()

    return election


@APP.route('/vote/<election_alias>', methods=['GET', 'POST'])
@login_required
def vote(election_alias):
    election = get_valid_election(election_alias)

    if not isinstance(election, models.Election):
        return election

    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    if votes > 0:
        flask.flash('You have already voted in the election!')
        return safe_redirect_back()

    if election.voting_type == 'range':
        return vote_range(election_alias)
    elif election.voting_type == 'simple':
        return vote_simple(election_alias)
    else:
        flask.flash(
            'Unknown election voting type: %s' % election.voting_type)
        return safe_redirect_back()


@APP.route('/vote_range/<election_alias>', methods=['GET', 'POST'])
@login_required
def vote_range(election_alias):
    election = get_valid_election(election_alias)

    if not isinstance(election, models.Election):
        return election

    if (election.voting_type == 'simple'):
        return flask.redirect(flask.url_for(
            'vote_simple', election_alias=election_alias))

    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    if votes > 0:
        flask.flash('You have already voted in the election!')
        return safe_redirect_back()

    num_candidates = election.candidates.count()

    uvotes = {}
    for candidate in election.candidates:
        uvotes[candidate.id] = ""
    next_action = 'vote'

    if flask.request.method == 'POST':
        next_action = ''
        form_values = flask.request.form.values()
        if 'Submit' in form_values:
            for candidate in election.candidates:
                try:
                    vote = int(flask.request.form[str(candidate.id)])
                    if vote >= 0 and vote <= num_candidates:
                        uvotes[candidate.id] = int(vote)
                    else:
                        flask.flash("Invalid Ballot!")
                        return safe_redirect_back()

                except ValueError:
                    flask.flash("Invalid Ballot!")
                    return safe_redirect_back()

            for uvote in uvotes:
                new_vote = models.Vote(
                    election_id=election.id,
                    voter=flask.g.fas_user.username,
                    timestamp=datetime.now(),
                    candidate_id=uvote,
                    value=uvotes[uvote]
                )
                SESSION.add(new_vote)
            SESSION.commit()

            flask.flash("Your vote has been recorded.  Thank you!")
            return safe_redirect_back()

        elif 'Preview' in form_values:
            flask.flash("Please confirm your vote!")
            for candidate in election.candidates:
                try:
                    vote = int(flask.request.form[str(candidate.id)])
                    if vote > num_candidates:
                        flask.flash("Invalid data.")
                        uvotes[candidate.id] = 0
                        next_action = 'vote'
                    elif vote >= 0:
                        uvotes[candidate.id] = vote
                    else:
                        flask.flash("Invalid data2.")
                        uvotes[c.id] = 0
                        next_action = 'vote'
                except ValueError:
                    flask.flash("Invalid data")

            if (next_action != 'vote'):
                next_action = 'confirm'

    usernamemap = {}
    if (election.candidates_are_fasusers):
        for candidate in election.candidates:
            try:
                usernamemap[candidate.id] = \
                    FAS2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    return flask.render_template(
        'vote_range.html',
        election=election,
        num_candidates=num_candidates,
        usernamemap=usernamemap,
        voteinfo=uvotes,
        nextaction=next_action)


@APP.route('/vote_simple/<election_alias>', methods=['GET', 'POST'])
@login_required
def vote_simple(election_alias):
    election = get_valid_election(election_alias)

    if not isinstance(election, models.Election):
        return election

    if (election.voting_type == 'range'):
        return flask.redirect(flask.url_for(
            'vote_range', election_alias=election_alias))

    votes = models.Vote.of_user_on_election(
        SESSION, flask.g.fas_user.username, election.id, count=True)

    if (votes != 0):
        flask.flash('You have already voted in the election!')
        return safe_redirect_back()

    num_candidates = election.candidates.count()
    next_action = 'vote'
    candidate_id = -1

    if flask.request.method == 'POST':
        next_action = ''
        form_values = flask.request.form.values()
        if 'Submit' in form_values:
            candidate_id = int(flask.request.form['candidate'])
            new_vote = models.Vote(
                election_id=election.id,
                voter=flask.g.fas_user.username,
                timestamp=datetime.now(),
                candidate_id=candidate_id,
                value=1
            )
            SESSION.add(new_vote)
            SESSION.commit()

            flask.flash("Your vote has been recorded.  Thank you!")
            return safe_redirect_back()

        elif 'Preview' in form_values:
            if ('candidate' in flask.request.form):
                flask.flash("Please confirm your vote!")
                candidate_id = int(flask.request.form['candidate'])
            else:
                flask.flash("Please vote for a candidate")
                next_action = 'vote'

        if (next_action != 'vote'):
            next_action = 'confirm'

    usernamemap = {}
    if (election.candidates_are_fasusers):
        for candidate in election.candidates:
            try:
                usernamemap[candidate.id] = \
                    FAS2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    return flask.render_template(
        'vote_simple.html',
        election=election,
        num_candidates=num_candidates,
        usernamemap=usernamemap,
        candidate_id=candidate_id,
        nextaction=next_action)


@APP.route('/results/<election_alias>')
def election_results(election_alias):
    election = get_valid_election(election_alias, ended=True)

    if not isinstance(election, models.Election):
        return election

    elif election.embargoed:
        if not hasattr(flask.g, 'fas_user') or not flask.g.fas_user:
            flask.flash("We are sorry.  The results for this election "
                        "cannot be viewed because they are currently "
                        "embargoed pending formal announcement.")
            return safe_redirect_back()
        else:
            if is_admin(flask.g.fas_user) \
                    or is_election_admin(flask.g.fas_user, election.id):
                flask.flash("You are only seeing this page because you are "
                            "an admin.", "warning")
                flask.flash("The results for this election are currently "
                            "embargoed pending formal announcement.",
                            "warning")
                pass
            else:
                flask.flash(
                    "We are sorry.  The results for this election "
                    "cannot be viewed because they are currently "
                    "embargoed pending formal announcement.")
                return safe_redirect_back()

    usernamemap = {}
    if (election.candidates_are_fasusers):
        for candidate in election.candidates:
            try:
                usernamemap[candidate.id] = \
                    FAS2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    stats = models.Vote.get_election_stats(SESSION, election.id)

    return flask.render_template(
        'results.html',
        election=election,
        usernamemap=usernamemap,
        stats=stats,
    )
