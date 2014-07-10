#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Pierre-Yves Chibon
 Author: Pierre-Yves Chibon <pingou@pingoured.fr>

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

 fedora_elections test script
"""

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import logging
import unittest
import sys
import os

from datetime import date
from datetime import timedelta
from functools import wraps

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedora_elections
import fedora_elections.admin
import fedora_elections.elections
import fedora_elections.forms
from fedora_elections import models


DB_PATH = 'sqlite:///:memory:'
FAITOUT_URL = 'http://209.132.184.152/faitout/'
if os.environ.get('BUILD_ID'):
    try:
        import requests
        req = requests.get('%s/new' % FAITOUT_URL)
        if req.status_code == 200:
            DB_PATH = req.text
            print 'Using faitout at: %s' % DB_PATH
    except:
        pass


TODAY = date.today()


@contextmanager
def user_set(APP, user):
    """ Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask.ext.fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    from flask import appcontext_pushed, g
    APP.before_request_funcs[None] = []

    def handler(sender, **kwargs):
        g.fas_user = user

    with appcontext_pushed.connected_to(handler, APP):
        yield


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self.session = models.create_tables(DB_PATH)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        self.session.close()
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        if DB_PATH.startswith('postgres'):
            if 'localhost' in DB_PATH:
                models.drop_tables(DB_PATH, self.session.bind)
            else:
                db_name = DB_PATH.rsplit('/', 1)[1]
                requests.get('%s/clean/%s' % (FAITOUT_URL, db_name))


class ModelFlasktests(Modeltests):
    """ Model flask application tests. """

    def setup_db(self):
        """ Add a calendar and some meetings so that we can play with
        something. """
        from test_vote import Votetests
        votes = Votetests('test_init_vote')
        votes.session = self.session
        votes.test_init_vote()

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(ModelFlasktests, self).setUp()

        fedora_elections.APP.config['TESTING'] = True
        fedora_elections.APP.config[
            'FEDORA_ELECTIONS_ADMIN_GROUP'] = 'elections'
        fedora_elections.APP.debug = True
        fedora_elections.APP.logger.handlers = []
        fedora_elections.APP.logger.setLevel(logging.CRITICAL)
        fedora_elections.SESSION = self.session

        fedora_elections.admin.SESSION = self.session
        fedora_elections.elections.SESSION = self.session
        fedora_elections.forms.SESSION = self.session

        self.app = fedora_elections.APP.test_client()


class FakeGroup(object):
    """ Fake object used to make the FakeUser object closer to the
    expectations.
    """

    def __init__(self, name):
        """ Constructor.
        :arg name: the name given to the name attribute of this object.
        """
        self.name = name
        self.group_type = 'cla'


# pylint: disable=R0903
class FakeUser(object):
    """ Fake user used to test the fedocallib library. """

    def __init__(self, groups=[], username='username', cla_done=True):
        """ Constructor.
        :arg groups: list of the groups in which this fake user is
            supposed to be.
        """
        if isinstance(groups, basestring):
            groups = [groups]
        self.groups = groups
        self.username = username
        self.name = username
        self.approved_memberships = [
            FakeGroup('packager'),
            FakeGroup('design-team')]
        self.dic = {}
        self.dic['timezone'] = 'Europe/Paris'
        self.cla_done = cla_done

    def __getitem__(self, key):
        return self.dic[key]


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
