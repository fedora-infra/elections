# -*- coding: utf-8 -*-
#
# Copyright © 2012-2015  Red Hat, Inc.
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
from __future__ import unicode_literals, absolute_import

__version__ = '2.9'

import logging  # noqa
import os  # noqa
import sys  # noqa
import urllib  # noqa
import hashlib  # noqa
import arrow  # noqa


from datetime import datetime, time, timedelta  # noqa
from functools import wraps  # noqa
from six.moves.urllib.parse import urlparse, urljoin, urlencode  # noqa

import flask  # noqa
import munch  # noqa
import six  # noqa

from fasjson_client import Client
from fedora.client import AuthError, AppError  # noqa
from fedora.client.fas2 import AccountSystem  # noqa
from flask_oidc import OpenIDConnect  # noqa

import fedora_elections.fedmsgshim  # noqa
import fedora_elections.proxy  # noqa

APP = flask.Flask(__name__)
APP.config.from_object('fedora_elections.default_config')
if 'FEDORA_ELECTIONS_CONFIG' in os.environ:  # pragma: no cover
    APP.config.from_envvar('FEDORA_ELECTIONS_CONFIG')

# set up FAS
OIDC = OpenIDConnect(APP, credentials_store=flask.session)

logging.basicConfig()
logging.config.dictConfig(APP.config.get("LOGGING") or {"version": 1})
LOG = APP.logger

APP.wsgi_app = fedora_elections.proxy.ReverseProxied(APP.wsgi_app)

if APP.config.get('FASJSON'):
    ACCOUNTS = Client(
        url=APP.config['FAS_BASE_URL']
    )
else:
    # FAS for usernames.
    ACCOUNTS = AccountSystem(
        APP.config['FAS_BASE_URL'],
        username=APP.config['FAS_USERNAME'],
        password=APP.config['FAS_PASSWORD'],
        insecure=not APP.config['FAS_CHECK_CERT']
    )


# modular imports
from fedora_elections import models  # noqa
SESSION = models.create_session(APP.config['DB_URL'])
from fedora_elections import forms  # noqa


from fedora_elections.utils import build_name_map  # noqa


def is_authenticated():
    ''' Return a boolean specifying if the user is authenticated or not.
    '''
    return hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None


def is_safe_url(target):
    """ Checks that the target url is safe and sending to the current
    website not some other malicious one.
    """
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def is_admin(user, user_groups=None):
    ''' Is the user an elections admin.
    '''
    if not user_groups:
        user_groups = []

    if not user:
        return False
    if not user.cla_done:
        return False

    user_groups = []
    if is_authenticated() and OIDC.user_loggedin:
        user_groups = OIDC.user_getfield('groups')

    if len(user_groups) < 1:
        return False

    admins = APP.config['FEDORA_ELECTIONS_ADMIN_GROUP']
    if isinstance(admins, six.string_types):  # pragma: no cover
        admins = set([admins])
    else:
        admins = set(admins)

    return len(set(user_groups).intersection(admins)) > 0


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
    if is_authenticated() and OIDC.user_loggedin:
        user = flask.g.fas_user
    return dict(is_admin=is_admin(user),
                version=__version__)


@APP.template_filter('rjust')
def rjust_filter(text, length):
    """ Run a rjust command on the text for the given length
    """
    return str(text).rjust(length)


@APP.template_filter('avatar')
def avatar_filter(openid, size=64, default='retro'):
    query = urlencode({'s': size, 'd': default})
    openid = openid.encode("utf-8")
    hashhex = hashlib.sha256(openid).hexdigest()
    return "https://seccdn.libravatar.org/avatar/%s?%s" % (hashhex, query)


@APP.template_filter('humanize')
def humanize_date(date):
    return arrow.get(date).humanize()


@APP.template_filter('prettydate')
def prettydate(date):
    return date.strftime('%A %B %d %Y %X UTC')


# pylint: disable=W0613
@APP.before_request
def set_session():  # pragma: no-cover
    """ Set the flask session as permanent. """
    flask.session.permanent = True

    if OIDC.user_loggedin:
        if not hasattr(flask.session, 'fas_user') \
                or not flask.session.fas_user:
            flask.session.fas_user = munch.Munch({
                'username': OIDC.user_getfield('nickname'),
                'email': OIDC.user_getfield('email') or '',
                'timezone': OIDC.user_getfield('zoneinfo'),
                'cla_done':
                    'FPCA'
                    in (OIDC.user_getfield('agreements') or []),
            })
        flask.g.fas_user = flask.session.fas_user
    else:
        flask.session.fas_user = None
        flask.g.fas_user = None


# pylint: disable=W0613
@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()


# LIST VIEWS #############################################

@APP.route('/')
def index():
    now = datetime.utcnow()

    prev_elections = models.Election.get_older_election(SESSION, now)[:5]
    cur_elections = models.Election.get_open_election(SESSION, now)
    next_elections = models.Election.get_next_election(SESSION, now)

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
    stats = []
    evolution_label = []
    evolution_data = []
    if not election:
        flask.flash('The election, %s,  does not exist.' % election_alias)
        return safe_redirect_back()
    elif election.status in ['Embargoed', 'Ended']:

        stats = models.Vote.get_election_stats(SESSION, election.id)
        cnt = 1
        for delta in range((election.end_date - election.start_date).days + 1):
            day = (
                election.start_date + timedelta(days=delta)
            ).strftime('%d-%m-%Y')
            evolution_label.append([cnt, day])
            evolution_data.append([cnt, stats['vote_timestamps'].count(day)])
            cnt += 1

    usernamemap = build_name_map(election)

    voted = []
    if is_authenticated():
        votes = models.Vote.of_user_on_election(
            SESSION, flask.g.fas_user.username, election.id, count=True)
        if votes > 0:
            voted.append(election)

    return flask.render_template(
        'about.html',
        election=election,
        usernamemap=usernamemap,
        stats=stats,
        voted=voted,
        evolution_label=evolution_label,
        evolution_data=evolution_data,
        candidates=sorted(
            election.candidates, key=lambda x: x.vote_count, reverse=True),
    )


@APP.route('/archives')
def archived_elections():
    now = datetime.utcnow()

    old_elections = models.Election.get_older_election(SESSION, now)

    if not old_elections:
        flask.flash('There are no archived elections.')
        return safe_redirect_back()

    return flask.render_template(
        'archive.html',
        elections=old_elections)


@APP.route('/login', methods=('GET', 'POST'))
@OIDC.require_login
def auth_login():
    next_url = None
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            next_url = flask.request.args['next']

    if not next_url or next_url == flask.url_for('.auth_login'):
        next_url = flask.url_for('.index')

    return safe_redirect_back(next_url)


@APP.route('/logout')
def auth_logout():
    if hasattr(flask.g, 'fas_user') and flask.g.fas_user is not None:
        OIDC.logout()
        flask.g.fas_user = None
        flask.session.fas_user = None
        flask.flash('You have been logged out')
    return safe_redirect_back()


# Finalize the import of other controllers
import fedora_elections.admin  # noqa
import fedora_elections.elections  # noqa
