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

__version__ = '2.1'

import os

from datetime import datetime, time
from functools import wraps
from urlparse import urlparse, urljoin

import flask

from fedora.client import AuthError, AppError
from fedora.client.fas2 import AccountSystem
from flask.ext.fas_openid import FAS

import fedora_elections.fedmsgshim
import fedora_elections.proxy

APP = flask.Flask(__name__)
APP.config.from_object('fedora_elections.default_config')
if 'FEDORA_ELECTIONS_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('FEDORA_ELECTIONS_CONFIG')

# set up FAS
FAS = FAS(APP)
APP.wsgi_app = fedora_elections.proxy.ReverseProxied(APP.wsgi_app)

# FAS for usernames.
FAS2 = AccountSystem(
    APP.config['FAS_BASE_URL'],
    username=APP.config['FAS_USERNAME'],
    password=APP.config['FAS_PASSWORD'],
    insecure=not APP.config['FAS_CHECK_CERT']
)


# modular imports
from fedora_elections import models
SESSION = models.create_session(APP.config['DB_URL'])
from fedora_elections import forms


def is_authenticated():
    ''' Return a boolean specifying if the user is authenticated or not.
    '''
    return hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None


def is_safe_url(target):
    """ Checks that the target url is safe and sending to the current
    website not some other malicious one.
    """
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(
        urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def is_admin(user):
    ''' Is the user an elections admin.
    '''
    if not user:
        return False
    if not user.cla_done or len(user.groups) < 1:
        return False

    admins = APP.config['FEDORA_ELECTIONS_ADMIN_GROUP']
    if isinstance(admins, basestring):  # pragma: no cover
        admins = set([admins])
    else:
        admins = set(admins)

    return len(set(user.groups).intersection(admins)) > 0


def is_election_admin(user, election_id):
    ''' Check if the provided user is in one of the admin group of the
    specified election.
    '''
    if not user:
        return False
    if not user.cla_done or len(user.groups) < 1:
        return False
    if is_admin(user):
        return True

    admingroups = [
        group.group_name
        for group in models.ElectionAdminGroup.by_election_id(
            SESSION, election_id=election_id)
        ]

    return len(set(user.groups).intersection(set(admingroups))) > 0


def is_safe_url(target):
    ''' Check is a url is safe to use or not. '''
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def safe_redirect_back(next=None, fallback=('index', {})):
    ''' Safely redirect the user to its previous page. '''
    targets = []
    if next:  # pragma: no cover
        targets.append(next)
    if 'next' in flask.request.args and \
       flask.request.args['next']:  # pragma: no cover
        targets.append(flask.request.args['next'])
    targets.append(flask.url_for(fallback[0], **fallback[1]))
    for target in targets:
        if is_safe_url(target):
            return flask.redirect(target)


@APP.context_processor
def inject_variables():
    ''' Inject a set of variable that we want for every pages (every
    template).
    '''
    user = None
    if hasattr(flask.g, 'fas_user'):
        user = flask.g.fas_user
    return dict(is_admin=is_admin(user),
                version=__version__)


# LIST VIEWS #############################################

@APP.route('/')
def index():
    now = datetime.utcnow()

    prev_elections = models.Election.get_older_election(SESSION, now)[:5]
    cur_elections = models.Election.get_open_election(SESSION, now)
    next_elections = models.Election.get_next_election(SESSION, now)[:3]

    voted = []
    if is_authenticated():
        for elec in cur_elections:
            votes = models.Vote.of_user_on_election(
                SESSION, flask.g.fas_user.username, elec.id, count=True)
            if votes > 0:
                voted.append(elec)

    return flask.render_template(
        'index.html',
        prev_elections=prev_elections,
        cur_elections=cur_elections,
        next_elections=next_elections,
        voted=voted,
        tag='index',
        title="Elections")


@APP.route('/about/<election_alias>')
def about_election(election_alias):
    election = models.Election.get(SESSION, alias=election_alias)

    if not election:
        flask.flash('The election, %s,  does not exist.' % election_alias)
        return safe_redirect_back()

    usernamemap = {}
    if (election.candidates_are_fasusers):  # pragma: no cover
        for candidate in election.candidates:
            try:
                usernamemap[candidate.id] = \
                    FAS2.person_by_username(candidate.name)['human_name']
            except (KeyError, AuthError):
                # User has their name set to private or user doesn't exist.
                usernamemap[candidate.id] = candidate.name

    return flask.render_template(
        'about.html',
        election=election,
        usernamemap=usernamemap)


@APP.route('/archives')
def archived_elections():
    now = datetime.utcnow()

    elections = models.Election.get_older_election(SESSION, now)

    if not elections:
        flask.flash('There are no archived elections.')
        return safe_redirect_back()

    return flask.render_template(
        'archive.html',
        elections=elections)


@APP.route('/open')
def open_elections():
    now = datetime.utcnow()

    elections = models.Election.get_open_election(SESSION, now)

    if not elections:
        flask.flash('There are no open elections.')
        return safe_redirect_back()

    voted = []
    if is_authenticated():
        for elec in elections:
            votes = models.Vote.of_user_on_election(
                SESSION, flask.g.fas_user.username, elec.id, count=True)
            if votes > 0:
                voted.append(elec)

    return flask.render_template(
        'index.html',
        next_elections=elections,
        voted=voted,
        tag='open',
        title='Open Elections')


@APP.route('/login', methods=('GET', 'POST'))
def auth_login():
    next_url = None
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for('.auth_login'):
        next_url = flask.url_for('.index')

    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        return safe_redirect_back(next_url)
    else:
        return FAS.login(return_url=next_url)


@APP.route('/logout')
def auth_logout():
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        FAS.logout()
        flask.g.fas_user = None
        flask.flash('You have been logged out')
    return safe_redirect_back()


# Finalize the import of other controllers
import admin
import elections
