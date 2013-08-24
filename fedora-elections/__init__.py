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
#

import flask
from flask.ext.fas import FAS
from flask.ext.sqlalchemy import SQLAlchemy

from fedora.client import AuthError, AppError
from fedora.client.fas2 import AccountSystem

from sqlalchemy.orm.exc import NoResultFound

import fedmsgshim

from datetime import datetime, time
from functools import wraps
from urlparse import urlparse, urljoin

app = flask.Flask(__name__)
app.config.from_object('fedora_elections.default_config')
app.config.from_envvar('FEDORA_ELECTIONS_CONFIG')

# set up SQLAlchemy
db = SQLAlchemy(app)

# set up FAS
fas = FAS(app)

# FAS for usernames.
# baseURL = "https://admin.fedoraproject.org/accounts"
# fasuser = "elections"
# faspw = "elections"
# fas2_url = 'http://fakefas.fedoraproject.org/accounts/'
fas2_url = app.config['FAS_BASE_URL']
fas2_username = app.config['FAS_USERNAME']
fas2_password = app.config['FAS_PASSWORD']
fas2 = AccountSystem(fas2_url, username=fas2_username, password=fas2_password,
                     insecure=True)


# modular imports
from fedora_elections import forms, models, redirect


def remove_csrf(form_data):
    return dict([(k, v) for k, v in form_data.items() if k != 'csrf'])


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.g.fas_user is None:
            return flask.redirect(flask.url_for('auth_login',
                                                next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


def election_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.g.fas_user is None:
            return flask.redirect(flask.url_for('auth_login',
                                                next=flask.request.url))
        if app.config['FEDORA_ELECTIONS_ADMIN_GROUP'] not in \
           flask.g.fas_user.groups:
            flask.abort(403)
        return f(*args, **kwargs)
    return decorated_function


### LIST VIEWS #############################################

@app.route('/')
def index():
    elections = models.Election.query.filter_by(frontpage=True).all()
    num_elections = len(elections)
    return flask.render_template('list/index.html', elections=elections,
                                 num_elections=num_elections,
                                 title="Elections")


@app.route('/about/<election_alias>')
def about_election(election_alias):
    try:
        election = models.Election.query.filter_by(alias=election_alias).one()
    except NoResultFound:
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

    return flask.render_template('election/about.html', election=election,
                                 usernamemap=usernamemap)


@app.route('/archive')
def archived_elections():
    now = datetime.utcnow()

    try:
        elections = models.Election.query.order_by(models.Election.start_date).\
                        filter(models.Election.end_date<now, models.Election.id>0).all()
    except NoResultFound:
        flask.flash('There are no archived elections.')
        return redirect.safe_redirect_back()

    num_elections = len(elections)
    if (num_elections == 0):
        flask.flash('There are no open elections.')
        return redirect.safe_redirect_back()

    return flask.render_template('election/archive.html',
                                 num_elections=num_elections,
                                 elections=elections)


@app.route('/open')
def open_elections():
    now = datetime.utcnow()

    try:
        elections = models.Election.query.order_by(models.Election.start_date).\
                        filter(models.Election.end_date>now,
                               models.Election.id>0).all()
    except NoResultFound:
        flask.flash('There are no open elections.')
        return redirect.safe_redirect_back()

    num_elections = models.Election.query.order_by(models.Election.start_date).\
                        filter(models.Election.end_date>now,
                               models.Election.id>0).count()
    if (num_elections == 0):
        flask.flash('There are no open elections.')
        return redirect.safe_redirect_back()

    return flask.render_template('list/index.html', elections=elections,
                                 num_elections=num_elections,
                                 title='Open Elections')


### ELECTION VIEWS #############################################

@app.route('/vote/<election_alias>', methods=['GET', 'POST'])
def vote(election_alias):
    try:
        election = models.Election.query.filter_by(alias=election_alias).one()
    except NoResultFound:
        flask.flash('The election, %s,  does not exist.' % election_alias)
        return redirect.safe_redirect_back()

    if election.status == 'Pending':
        flask.flash('Voting has not yet started, sorry.')
        return redirect.safe_redirect_back()

    elif election.status == 'Ended':
        flask.flash('This election is closed.  You have been redirected to ' +
                    'the election results.')
        return flask.redirect(flask.url_for('results', election.shortname))

    votes = models.Vote.query.filter_by(election_id=election.id,
                                         voter=flask.g.fas_user.username).count()
    if (votes != 0):
        flask.flash('You have already voted in the election!')
        return redirect.safe_redirect_back()

    num_candidates = election.candidates.count()

    uvotes = {}
    for candidate in election.candidates:
        uvotes[candidate.id] = ""
    next_action =  'vote'

    if flask.request.method == 'POST':
        next_action =  ''
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
                new_vote = models.Vote(election_id=election.id,
                                       voter=flask.g.fas_user.username,
                                       timestamp=datetime.now(),
                                       candidate_id=uvote,
                                       value=uvotes[uvote] )
                db.session.add(new_vote)
                db.session.commit()

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

    return flask.render_template('election/vote.html', election=election,
                                 num_candidates=num_candidates,
                                 usernamemap=usernamemap,
                                 voteinfo=uvotes, nextaction=next_action)


### AUTH VIEWS #############################################

@app.route('/login', methods=('GET', 'POST'))
def auth_login():
    if flask.g.fas_user:
        return redirect.safe_redirect_back()
    form = forms.LoginForm()
    if form.validate_on_submit():
        if fas.login(form.username.data, form.password.data):
            flask.flash('Welcome, %s' % flask.g.fas_user.username)
            return redirect.safe_redirect_back()
        else:
            flask.flash('Incorrect username or password')
    return flask.render_template('auth/login.html', form=form)


@app.route('/logout')
def auth_logout():
    if not flask.g.fas_user:
        return redirect.safe_redirect_back()
    fas.logout()
    flask.flash('You have been logged out')
    return redirect.safe_redirect_back()


### ELECTION ADMIN VIEWS ###################################

@app.route('/admin/')
@election_admin_required
def admin_view_elections():
    elections = models.Election.query.\
                    filter_by(fas_user=flask.g.fas_user.username).all()
    num_elections = len(elections)
    if (num_elections == 0):
        flask.flash('You do not have any elections.')
        return redirect.safe_redirect_back()

    return flask.render_template('admin/all_elections.html',
                                 num_elections=num_elections,
                                 elections=elections)


@app.route('/admin/new', methods=("GET", "POST"))
@election_admin_required
def admin_new_election():
    form = forms.ElectionForm()
    if form.validate_on_submit():
        election = models.Election(**remove_csrf(form.data))
        # Fix start_date and end_date to use datetime
        election.start_date = datetime.combine(election.start_date, time())
        election.end_date = datetime.combine(election.end_date,
                                             time(23, 59, 59))
        election.fas_user = flask.g.fas_user.username
        db.session.add(election)
        admin = models.ElectionAdminGroup(election=election,
                                          group_name=app.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
                                          role_required=u'user')
        db.session.add(admin)
        db.session.commit()
        flask.flash('Election "%s" added' % election.summary)
        fedmsgshim.publish(topic="election.new", msg=election)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/election_form.html', form=form,
                                 submit_text='Create election')


@app.route('/admin/<election_alias>/')
@election_admin_required
def admin_view_election(election_alias):
    election = models.Election.query.filter_by(alias=election_alias).first()
    if not election:
        flask.abort(404)
    return flask.render_template('admin/view_election.html', election=election)


@app.route('/admin/<election_alias>/edit', methods=("GET", "POST"))
@election_admin_required
def admin_edit_election(election_alias):
    election = models.Election.query.filter_by(alias=election_alias).first()
    if not election:
        flask.abort(404)
    form = forms.ElectionForm(election.id, obj=election)
    if form.validate_on_submit():
        form.populate_obj(election)
        db.session.commit()
        flask.flash('Election "%s" saved' % election.summary)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/election_form.html', form=form,
                                 submit_text='Edit election')


@app.route('/admin/<election_alias>/candidates/new', methods=("GET", "POST"))
@election_admin_required
def admin_add_candidate(election_alias):
    election = models.Election.query.filter_by(alias=election_alias).first()
    if not election:
        flask.abort(404)
    form = forms.CandidateForm()
    if form.validate_on_submit():
        candidate = models.Candidate(election=election,
                                     **remove_csrf(form.data))
        db.session.add(candidate)
        db.session.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/candidate.html', form=form,
                                 submit_text='Add candidate')


@app.route('/admin/<election_alias>/candidates/<int:candidate_id>/edit',
           methods=("GET", "POST"))
@election_admin_required
def admin_edit_candidate(election_alias, candidate_id):
    election = models.Election.query.filter_by(alias=election_alias).first()
    candidate = models.Candidate.query.filter_by(id=candidate_id).first()
    if not election or not candidate:
        flask.abort(404)
    if candidate.election != election:
        flask.abort(404)
    form = forms.CandidateForm(obj=candidate)
    if form.validate_on_submit():
        form.populate_obj(candidate)
        db.session.commit()
        flask.flash('Candidate "%s" saved' % candidate.name)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/candidate.html', form=form,
                                 submit_text='Edit candidate')


@app.route('/admin/<election_alias>/candidates/<int:candidate_id>/delete',
           methods=("GET", "POST"))
@election_admin_required
def admin_delete_candidate(election_alias, candidate_id):
    election = models.Election.query.filter_by(alias=election_alias).first()
    candidate = models.Candidate.query.filter_by(id=candidate_id).first()
    if not election or not candidate:
        flask.abort(404)
    if candidate.election != election:
        flask.abort(404)
    form = forms.ConfirmationForm()
    if form.validate_on_submit():
        db.session.delete(candidate)
        candidate_name = candidate.name
        db.session.commit()
        flask.flash('Candidate "%s" deleted' % candidate_name)
        return flask.redirect(flask.url_for('admin_view_election',
                                            election_alias=election.alias))
    return flask.render_template('admin/delete_candidate.html', form=form,
                                 candidate=candidate)


@app.route('/results/<election_alias>')
def election_results(election_alias):
    try:
        election = models.Election.query.filter_by(alias=election_alias).one()
    except NoResultFound:
        flask.flash('The election, %s,  does not exist.' % election_alias)
        return redirect.safe_redirect_back()

    if election.status == 'In progress':
        flask.flash("We are sorry.  The results for this election cannot be" \
                    " viewed at this time because the election is still in" \
                    " progress.")
        return redirect.safe_redirect_back()

    elif election.status == 'Pending':
        flask.flash("We are sorry.  The results for this election cannot be" \
                    " viewed at this time because the election has not" \
                    " started.")
        return redirect.safe_redirect_back()

    elif election.embargoed == 1:
        if flask.g.fas_user is None:
                flask.flash("We are sorry.  The results for this election" \
                            "cannot be viewed because they are currently" \
                            " embargoed pending formal announcement.")
                return redirect.safe_redirect_back()
        else:
            if app.config['FEDORA_ELECTIONS_ADMIN_GROUP'] in \
	       flask.g.fas_user.groups:
                pass
            else:
                match = 0
                admingroups = models.ElectionAdminGroup.query.filter_by(
                              election_id=election.id).all()
                for admingroup in admingroups:
	            if admingroup.group_name in flask.g.fas_user.groups:
                        match = 1

                if match == 0:
                    flask.flash("We are sorry.  The results for this election" \
                                "cannot be viewed because they are currently" \
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

    return flask.render_template('election/results.html', election=election,
                                 usernamemap=usernamemap)
