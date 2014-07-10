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

 fedora_elections.model.Election test script
"""
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import unittest
import sys
import os

from datetime import time
from datetime import timedelta

import flask

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedora_elections
from tests import ModelFlasktests, FakeUser, user_set


# pylint: disable=R0904
class Flasktests(ModelFlasktests):
    """ Flask application tests. """

    def test_index_empty(self):
        """ Test the index function. """
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title>Fedora elections</title>' in output.data)
        self.assertFalse('<h3>Current elections</h3>' in output.data)
        self.assertFalse('<h3>Next' in output.data)
        self.assertFalse('<h3>Last' in output.data)
        self.assertTrue('<a href="/login">login</a>' in output.data)

        user = FakeUser([], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)
            self.assertTrue(
                '<span class="text">logged in as </span>' in output.data)

    def test_index_filled(self):
        """ Test the index function. """
        self.setup_db()
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title>Fedora elections</title>' in output.data)
        self.assertTrue('<h3>Current elections</h3>' in output.data)
        self.assertTrue('<h3>Next 1 elections</h3>' in output.data)
        self.assertTrue('<h3>Last 2 elections</h3>' in output.data)
        self.assertTrue('<a href="/login">login</a>' in output.data)

        user = FakeUser([], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)
            self.assertTrue('<h3>Next 1 elections</h3>' in output.data)
            self.assertTrue('<h3>Last 2 elections</h3>' in output.data)
            self.assertTrue('<a href="/vote/' in output.data)
            self.assertTrue(
                '<span class="text">logged in as </span>' in output.data)
            self.assertTrue('Vote now!' in output.data)

        user = FakeUser([], username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)
            self.assertTrue('<h3>Next 1 elections</h3>' in output.data)
            self.assertTrue('<h3>Last 2 elections</h3>' in output.data)
            self.assertTrue(
                '<span class="text">logged in as </span>' in output.data)
            self.assertFalse('Vote now!' in output.data)

    def test_is_admin(self):
        """ Test the is_admin function. """
        app = flask.Flask('fedora_elections')

        with app.test_request_context():
            flask.g.fas_user = None
            self.assertFalse(fedora_elections.is_admin(flask.g.fas_user))

            flask.g.fas_user = FakeUser()
            self.assertFalse(fedora_elections.is_admin(flask.g.fas_user))

            flask.g.fas_user = FakeUser(
                fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'])
            self.assertTrue(fedora_elections.is_admin(flask.g.fas_user))

            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'] = [
                'sysadmin-main', 'sysadmin-elections']
            flask.g.fas_user = FakeUser(
                fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'])
            self.assertTrue(fedora_elections.is_admin(flask.g.fas_user))

    def test_is_election_admin(self):
        """ Test the is_election_admin function. """
        app = flask.Flask('fedora_elections')

        with app.test_request_context():
            flask.g.fas_user = None
            self.assertFalse(
                fedora_elections.is_election_admin(
                    flask.g.fas_user, 1)
            )
            flask.g.fas_user = FakeUser()
            self.assertFalse(
                fedora_elections.is_election_admin(
                    flask.g.fas_user, 1)
            )
            flask.g.fas_user = FakeUser(
                fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'])
            self.assertTrue(fedora_elections.is_election_admin(
                flask.g.fas_user, 1))

        self.setup_db()

        with app.test_request_context():
            flask.g.fas_user = FakeUser('testers')
            # This is user is not an admin for election #1
            self.assertFalse(
                fedora_elections.is_election_admin(
                    flask.g.fas_user, 1)
            )

            # This is user is an admin for election #2
            self.assertTrue(
                fedora_elections.is_election_admin(
                    flask.g.fas_user, 2)
            )

    def test_is_safe_url(self):
        """ Test the is_safe_url function. """
        app = flask.Flask('fedora_elections')
        with app.test_request_context():
            self.assertFalse(
                fedora_elections.is_safe_url('https://google.fr'))
            self.assertTrue(
                fedora_elections.is_safe_url('/admin/'))

    def test_auth_login(self):
        """ Test the auth_login function. """
        app = flask.Flask('fedora_elections')

        with app.test_request_context():
            flask.g.fas_user = FakeUser(['gitr2spec'])
            output = self.app.get('/login')
            self.assertEqual(output.status_code, 200)

            output = self.app.get('/login?next=http://localhost/')
            self.assertEqual(output.status_code, 200)

        self.setup_db()
        user = FakeUser([], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/login', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)

    def test_auth_logout(self):
        """ Test the auth_logout function. """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'])
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/logout', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)
            self.assertTrue(
                '<li class="message">You have been logged out</li>'
                in output.data)

        user = None
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/logout', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)
            self.assertFalse(
                '<li class="message">You have been logged out</li>'
                in output.data)

    def test_about_election(self):
        """ Test the about_election function. """
        self.setup_db()

        output = self.app.get('/about/blah')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/about/blah', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="message">The election, blah,  does not exist.</li>'
            in output.data)
        self.assertTrue('<title>Fedora elections</title>' in output.data)
        self.assertTrue('<h3>Current elections</h3>' in output.data)
        self.assertTrue('<h3>Next 1 elections</h3>' in output.data)
        self.assertTrue('<h3>Last 2 elections</h3>' in output.data)

        output = self.app.get('/about/test_election')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>Election Information</title>' in output.data)
        self.assertTrue(
            '<small><a href="https://fedoraproject.org/wiki/User:Toshio">'
            '[info]</a></small>' in output.data)
        self.assertTrue(
            '<small><a href="https://fedoraproject.org/wiki/User:Ralph">'
            '[info]</a></small>' in output.data)
        self.assertTrue(
            '<a href="/results/test_election">Show Results!</a>'
            in output.data)
        self.assertTrue('<a href="/login">login</a>' in output.data)

    def test_archived_election(self):
        """ Test the archived_elections function. """
        output = self.app.get('/archives')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/archives', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="message">There are no archived elections.</li>'
            in output.data)
        self.assertTrue('<title>Fedora elections</title>' in output.data)
        self.assertTrue('<h2>Elections</h2>' in output.data)

        self.setup_db()

        output = self.app.get('/archives')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title>Fedora elections</title>' in output.data)
        self.assertTrue('<h2>Past Elections</h2>' in output.data)
        self.assertTrue(
            '<td>test election 2 shortdesc</td>' in output.data)
        self.assertTrue(
            '<td>test election shortdesc</td>' in output.data)
        self.assertEqual(output.data.count('<a href="results/'), 2)
        self.assertEqual(output.data.count('<a href="about/'), 2)
        self.assertTrue('<a href="/login">login</a>' in output.data)

    def test_open_elections(self):
        """ Test the open_elections function. """
        output = self.app.get('/open')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/open', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="message">There are no open elections.</li>'
            in output.data)
        self.assertTrue('<title>Fedora elections</title>' in output.data)
        self.assertTrue('<h2>Elections</h2>' in output.data)

        self.setup_db()

        output = self.app.get('/open')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title>Fedora elections</title>' in output.data)
        self.assertTrue('<h3>Next 2 elections</h3>' in output.data)
        self.assertTrue('<td>test election 3 shortdesc</td>' in output.data)
        self.assertTrue('<a href="/vote/' in output.data)
        self.assertTrue('<a href="/login">login</a>' in output.data)

        user = FakeUser([], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/open')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)
            self.assertTrue('<h3>Next 2 elections</h3>' in output.data)
            self.assertTrue('<a href="/vote/' in output.data)
            self.assertTrue(
                '<span class="text">logged in as </span>' in output.data)
            self.assertTrue('Vote now!' in output.data)

        user = FakeUser([], username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/open')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Fedora elections</title>' in output.data)
            self.assertTrue('<h3>Next 2 elections</h3>' in output.data)
            self.assertTrue(
                '<span class="text">logged in as </span>' in output.data)
            self.assertFalse('Vote now!' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Flasktests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
