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

import flask
from flask.ext.fas_openid import FAS

from fedora.client import AuthError, AppError
from fedora.client.fas2 import AccountSystem

from sqlalchemy.orm.exc import NoResultFound

import fedmsgshim

from datetime import datetime, time
from functools import wraps
from urlparse import urlparse, urljoin

APP = flask.Flask(__name__)
APP.config.from_object('fedora_elections.default_config')
if APP.config.get('FEDORA_ELECTIONS_CONFIG') \
        and os.path.exists(APP.config['FEDORA_ELECTIONS_CONFIG']):
    APP.config.from_envvar('FEDORA_ELECTIONS_CONFIG')

# set up FAS
FAS = FAS(APP)

# FAS for usernames.
FAS2 = AccountSystem(
    APP.config['FAS_BASE_URL'],
    username=APP.config['FAS_USERNAME'],
    password=APP.config['FAS_PASSWORD'],
    insecure=APP.config['FAS_CHECK_CERT']
)


# modular imports
from fedora_elections import models
SESSION = models.create_session(APP.config['DB_URL'])
from fedora_elections import forms
from fedora_elections import redirect


def remove_csrf(form_data):
    return dict([(k, v) for k, v in form_data.items() if k != 'csrf'])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None:
            return flask.redirect(flask.url_for(
                'auth_login', next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


def election_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(flask.g, 'fas_user') or flask.g.fas_user is None:
            return flask.redirect(flask.url_for(
                'auth_login', next=flask.request.url))
        if APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'] not in \
           flask.g.fas_user.groups:
            flask.abort(403)
        return f(*args, **kwargs)
    return decorated_function


def get_valid_election(election_alias, ended=False):
    """ Return the election if it is valid (no pending, not ended).
    """
    election = models.Election.get(SESSION, alias=election_alias)

    if not election:
        flask.flash('The election, %s,  does not exist.' % election_alias)
        return redirect.safe_redirect_back()

    if election.status == 'Pending':
        flask.flash('Voting has not yet started, sorry.')
        return redirect.safe_redirect_back()

    elif not ended and election.status == 'Ended':
        flask.flash(
            'This election is closed.  You have been redirected to the '
            'election results.')
        return flask.redirect(flask.url_for(
            'election_results', election_alias=election.alias))

    elif ended and election.status == 'In progress':
        flask.flash(
            'Sorry but this election is in progress, you may not see its '
            'results already.')
        return redirect.safe_redirect_back()

    return election


### LIST VIEWS #############################################

@APP.route('/')
def index():
    elections = models.Election.search(SESSION, frontpage=True)
    num_elections = len(elections)
    return flask.render_template(
        'list/index.html',
        elections=elections,
        num_elections=num_elections,
        title="Elections")


@APP.route('/about/<election_alias>')
def about_election(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)

    if not election:
        flask.flash('The election, %s,  does not exist.' % election_alias)
        return redirect.safe_redirect_back()

    usernamemap = {}
    if (election.candidates_are_fasusers):
        for candidate in election.candidates:
            try:
                usernamemap[candidate.id] = \
                    fas2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    return flask.render_template(
        'election/about.html',
        election=election,
        usernamemap=usernamemap)


@APP.route('/archive')
def archived_elections():
    now = datetime.utcnow()

    elections = models.Election.get_older_election(SESSION, now)

    if not elections:
        flask.flash('There are no archived elections.')
        return redirect.safe_redirect_back()

    return flask.render_template(
        'election/archive.html',
        elections=elections)


@APP.route('/open')
def open_elections():
    now = datetime.utcnow()

    elections = models.Election.get_open_election(SESSION, now)

    if not elections:
        flask.flash('There are no open elections.')
        return redirect.safe_redirect_back()

    return flask.render_template(
        'list/index.html',
        elections=elections,
        title='Open Elections')


### ELECTION VIEWS #############################################

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
        return redirect.safe_redirect_back()

    if election.voting_type == 'range':
        return vote_range(election_alias)
    elif election.voting_type == 'simple':
        return vote_simple(election_alias)
    else:
        flask.flash(
            'Unknown election voting type: %s' % election.voting_type)
        return redirect.safe_redirect_back()


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
        return redirect.safe_redirect_back()

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
                        return redirect.safe_redirect_back()

                except ValueError:
                    flask.flash("Invalid Ballot!")
                    return redirect.safe_redirect_back()

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
            return redirect.safe_redirect_back()

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
                    fas2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    return flask.render_template(
        'election/vote_range.html',
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
        return redirect.safe_redirect_back()

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
            return redirect.safe_redirect_back()

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
                    fas2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    return flask.render_template(
        'election/vote_simple.html',
        election=election,
        num_candidates=num_candidates,
        usernamemap=usernamemap,
        candidate_id=candidate_id,
        nextaction=next_action)


### AUTH VIEWS #############################################

@APP.route('/login', methods=('GET', 'POST'))
def auth_login():
    if flask.g.fas_user:
        return redirect.safe_redirect_back()
    next_url = None
    if 'next' in flask.request.args:
        next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for('.auth_login'):
        next_url = flask.url_for('.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return flask.redirect(next_url)
    else:
        return FAS.login(return_url=next_url)


@APP.route('/logout')
def auth_logout():
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
        flask.flash('You have been logged out')
    return redirect.safe_redirect_back()


### ELECTION ADMIN VIEWS ###################################

@APP.route('/admin/')
@election_admin_required
def admin_view_elections():
    elections = models.Election.search(
        SESSION, fas_user=flask.g.fas_user.username)

    if not elections:
        flask.flash('You do not have any elections.')
        return redirect.safe_redirect_back()

    return flask.render_template(
        'admin/all_elections.html',
        elections=elections)


@APP.route('/admin/new', methods=('GET', 'POST'))
@election_admin_required
def admin_new_election():
    form = forms.ElectionForm()
    if form.validate_on_submit():

        election = models.Election(
            summary=form.summary.data,
            alias=form.alias.data,
            description=form.description.data,
            url=form.url.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            number_elected=form.number_elected.data,
            embargoed=form.embargoed.data,
            frontpage=form.frontpage.data,
            voting_type=form.voting_type.data,
            candidates_are_fasusers=form.candidates_are_fasusers.data,
            fas_user=flask.g.fas_user.username,
        )

        # Fix start_date and end_date to use datetime
        election.start_date = datetime.combine(election.start_date, time())
        election.end_date = datetime.combine(election.end_date,
                                             time(23, 59, 59))
        SESSION.add(election)

        admin = models.ElectionAdminGroup(
            election=election,
            group_name=APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            role_required=u'user')
        SESSION.add(admin)

        SESSION.commit()

        flask.flash('Election "%s" added' % election.summary)
        fedmsgshim.publish(topic="election.new", msg=election)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))
    return flask.render_template(
        'admin/election_form.html',
        form=form,
        submit_text='Create election')


@APP.route('/admin/<election_alias>/')
@election_admin_required
def admin_view_election(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)

    return flask.render_template(
        'admin/view_election.html',
        election=election)


@APP.route('/admin/<election_alias>/edit', methods=('GET', 'POST'))
@election_admin_required
def admin_edit_election(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)

    form = forms.ElectionForm(election.id, obj=election)
    if form.validate_on_submit():
        form.populate_obj(election)
        SESSION.commit()
        flask.flash('Election "%s" saved' % election.summary)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/election_form.html',
        form=form,
        submit_text='Edit election')


@APP.route('/admin/<election_alias>/candidates/new', methods=('GET', 'POST'))
@election_admin_required
def admin_add_candidate(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)
    if not election:
        flask.abort(404)

    form = forms.CandidateForm()
    if form.validate_on_submit():
        candidate = models.Candidate(
            election=election,
            name=form.name.data,
            url=form.url.data
        )

        SESSION.add(candidate)
        SESSION.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/candidate.html',
        form=form,
        submit_text='Add candidate')


@APP.route('/admin/<election_alias>/candidates/<int:candidate_id>/edit',
           methods=('GET', 'POST'))
@election_admin_required
def admin_edit_candidate(election_alias, candidate_id):
    election = models.Election.get(SESSION, alias=election_alias)
    candidate = models.Candidate.get(SESSION, candidate_id=candidate_id)

    if not election or not candidate:
        flask.abort(404)

    if candidate.election != election:
        flask.abort(404)

    form = forms.CandidateForm(obj=candidate)
    if form.validate_on_submit():
        form.populate_obj(candidate)
        SESSION.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/candidate.html',
        form=form,
        submit_text='Edit candidate')


@APP.route('/admin/<election_alias>/candidates/<int:candidate_id>/delete',
           methods=('GET', 'POST'))
@election_admin_required
def admin_delete_candidate(election_alias, candidate_id):
    election = models.Election.get(SESSION, alias=election_alias)
    candidate = models.Candidate.get(SESSION, candidate_id=candidate_id)

    if not election or not candidate:
        flask.abort(404)

    if candidate.election != election:
        flask.abort(404)

    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        candidate_name = candidate.name
        SESSION.delete(candidate)
        SESSION.commit()
        flask.flash('Candidate "%s" deleted' % candidate_name)
        return flask.redirect(flask.url_for(
            'admin_view_election', election_alias=election.alias))

    return flask.render_template(
        'admin/delete_candidate.html',
        form=form,
        candidate=candidate)


@APP.route('/results/<election_alias>')
def election_results(election_alias):
    election = get_valid_election(election_alias, ended=True)

    if not isinstance(election, models.Election):
        return election

    elif election.embargoed == 1:
        if not hasattr(flask.g, 'fas_user') or not flask.g.fas_user:
            flask.flash("We are sorry.  The results for this election"
                        "cannot be viewed because they are currently"
                        " embargoed pending formal announcement.")
            return redirect.safe_redirect_back()
        else:
            if APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'] in \
                    flask.g.fas_user.groups:
                pass
            else:
                match = 0
                admingroups = models.ElectionAdminGroup.by_election_id(
                    SESSION, election_id=election.id)
                for admingroup in admingroups:
                    if admingroup.group_name in flask.g.fas_user.groups:
                        match = 1

                if match == 0:
                    flask.flash(
                        "We are sorry.  The results for this election"
                        "cannot be viewed because they are currently"
                        " embargoed pending formal announcement.")
                    return redirect.safe_redirect_back()

    usernamemap = {}
    if (election.candidates_are_fasusers):
        for candidate in election.candidates:
            try:
                usernamemap[candidate.id] = \
                    fas2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    return flask.render_template(
        'election/results.html',
        election=election,
        usernamemap=usernamemap)
