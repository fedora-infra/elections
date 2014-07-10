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

 fedora_elections.admin test script
"""
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import logging
import unittest
import sys
import os

from datetime import time
from datetime import timedelta

import flask

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedora_elections
from tests import ModelFlasktests, Modeltests, TODAY, FakeUser, user_set


# pylint: disable=R0904
class FlaskAdmintests(ModelFlasktests):
    """ Flask application tests for the admin controller. """

    def test_admin(self):
        """ Test the admin function. """
        output = self.app.get('/admin/')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/admin/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data
            or 'discoveryfailure' in output.data)

        user = FakeUser([], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 403)

        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Election administration</h2>' in output.data)

    def test_admin_view_election(self):
        """ Test the admin_view_election function. """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/election_test/')
            self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<a href="/admin/test_election/edit">' in output.data)
            self.assertTrue(
                '<p>3 candidates found</p>' in output.data)

    def test_admin_new_election(self):
        """ Test the admin_new_election function. """
        self.setup_db()

        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/new')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Create election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)

            # No csrf provided
            data = {
                'alias': 'new_election',
                'shortdesc': 'new election shortdesc',
                'description': 'new election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY + timedelta(days=2),
                'end_date': TODAY + timedelta(days=4),
                'seats_elected': '2',
                'candidates_are_fasusers': False,
                'embargoed': True,
            }

            output = self.app.post('/admin/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Create election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Description missing
            data = {
                'alias': 'new_election',
                'shortdesc': 'new election shortdesc',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY + timedelta(days=2),
                'end_date': TODAY + timedelta(days=4),
                'seats_elected': '2',
                'candidates_are_fasusers': False,
                'embargoed': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Create election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)
            self.assertTrue(
                '<td class="error">This field is required.</td>'
                in output.data)

            # Invalid alias
            data = {
                'alias': 'new',
                'shortdesc': 'new election shortdesc',
                'description': 'new election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY + timedelta(days=2),
                'end_date': TODAY + timedelta(days=4),
                'seats_elected': 2,
                'candidates_are_fasusers': False,
                'embargoed': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Create election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)
            self.assertTrue(
                '<td class="error">The alias cannot be <code>new</code>.</td>'
                in output.data)

            # Invalid: end_date earlier than start_date
            data = {
                'alias': 'new_election',
                'shortdesc': 'new election shortdesc',
                'description': 'new election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY + timedelta(days=6),
                'end_date': TODAY + timedelta(days=4),
                'seats_elected': 2,
                'candidates_are_fasusers': False,
                'embargoed': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Create election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)
            self.assertTrue(
                'class="error">End date must be later than start date.</td>'
                in output.data)

            # Invalid: alias already taken
            data = {
                'alias': 'test_election',
                'shortdesc': 'new election shortdesc',
                'description': 'new election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY + timedelta(days=6),
                'end_date': TODAY + timedelta(days=4),
                'seats_elected': 2,
                'candidates_are_fasusers': False,
                'embargoed': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Create election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)
            self.assertTrue(
                '<td class="error">There is already another election with '
                'this alias.</td>' in output.data)

            # Invalid: shortdesc already taken
            data = {
                'alias': 'new_election',
                'shortdesc': 'test election shortdesc',
                'description': 'new election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY + timedelta(days=6),
                'end_date': TODAY + timedelta(days=4),
                'seats_elected': 2,
                'candidates_are_fasusers': False,
                'embargoed': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Create election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)
            self.assertTrue(
                '<td class="error">There is already another election with '
                'this summary.</td>' in output.data)

            # All good  -  max_votes is ignored as it is not a integer
            data = {
                'alias': 'new_election',
                'shortdesc': 'new election shortdesc',
                'description': 'new election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY + timedelta(days=2),
                'end_date': TODAY + timedelta(days=4),
                'seats_elected': 2,
                'candidates_are_fasusers': False,
                'embargoed': True,
                'admin_grp': 'testers, sysadmin-main,,',
                'lgl_voters': 'testers, packager,,',
                'max_votes': 'wrong',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/new', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Election "new_election" added</li>'
                in output.data)
            self.assertTrue(
                '<a href="/admin/new_election/edit">' in output.data)
            self.assertTrue(
                '<p>There are no candidates.</p>' in output.data)
            self.assertTrue(
                '<li>Admin groups: sysadmin-main, testers</li>'
                in output.data)
            self.assertTrue(
                '<li>Legal voters: packager, testers</li>'
                in output.data)

    def test_admin_edit_election(self):
        """ Test the admin_edit_election function. """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/edit')
            self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/edit')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Edit election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)

            data = {
                'alias': 'test_election',
                'shortdesc': 'test election shortdesc',
                'description': 'test election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY - timedelta(days=10),
                'end_date': TODAY - timedelta(days=8),
                'seats_elected': '2',
                'candidates_are_fasusers': False,
                'embargoed': False,
            }

            output = self.app.post('/admin/test_election/edit', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Edit election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'alias': 'test_election',
                'shortdesc': 'test election shortdesc',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY - timedelta(days=10),
                'end_date': TODAY - timedelta(days=8),
                'seats_elected': '2',
                'candidates_are_fasusers': False,
                'embargoed': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/admin/test_election/edit', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>Edit election</h2>' in output.data)
            self.assertTrue(
                'input id="shortdesc" name="shortdesc" type="text"'
                in output.data)
            self.assertTrue(
                '<td class="error">This field is required.</td>'
                in output.data)

            # Check election before edit
            output = self.app.get('/admin/test_election/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<p>3 candidates found</p>' in output.data)
            self.assertTrue('<li>Number elected: 1</li>' in output.data)

            data = {
                'alias': 'test_election',
                'shortdesc': 'test election shortdesc',
                'description': 'test election description',
                'voting_type': 'simple',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY - timedelta(days=10),
                'end_date': TODAY - timedelta(days=8),
                'seats_elected': '2',
                'candidates_are_fasusers': False,
                'embargoed': False,
                'max_votes': 'wrong',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Election "test_election" saved</li>'
                in output.data)
            # We edited the seats_elected from 1 to 2
            self.assertTrue(
                '<li>Number elected: 2</li>' in output.data)
            self.assertTrue(
                '<p>3 candidates found</p>'
                in output.data)

    def test_admin_edit_election_admin_groups(self):
        """ Test the admin_edit_election function when editing admin groups.
        """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/edit')
            self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election2/edit')
            self.assertEqual(output.status_code, 200)
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Edit Admin Group

            # Check election before edit
            output = self.app.get('/admin/test_election2/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<li>Number elected: 1</li>' in output.data)
            self.assertTrue('<li>Admin groups: testers</li>' in output.data)

            # Add a new admin group: sysadmin-main
            data = {
                'alias': 'test_election2',
                'shortdesc': 'test election 2 shortdesc',
                'description': 'test election 2 description',
                'voting_type': 'range',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY - timedelta(days=7),
                'end_date': TODAY - timedelta(days=5),
                'seats_elected': '2',
                'candidates_are_fasusers': False,
                'embargoed': False,
                'admin_grp': 'testers, sysadmin-main',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election2/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Election "test_election2" saved</li>'
                in output.data)
            self.assertTrue(
                '<li>Number elected: 2</li>' in output.data)
            # We edited the admin groups
            self.assertTrue(
                '<li>Admin groups: sysadmin-main, testers</li>'
                in output.data)

            # Remove an existing group: testers
            data = {
                'alias': 'test_election2',
                'shortdesc': 'test election 2 shortdesc',
                'description': 'test election 2 description',
                'voting_type': 'range',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY - timedelta(days=7),
                'end_date': TODAY - timedelta(days=5),
                'seats_elected': '2',
                'candidates_are_fasusers': False,
                'embargoed': False,
                'admin_grp': 'sysadmin-main',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election2/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Election "test_election2" saved</li>'
                in output.data)
            self.assertTrue(
                '<li>Number elected: 2</li>' in output.data)
            # We edited the admin groups
            self.assertTrue(
                '<li>Admin groups: sysadmin-main</li>'
                in output.data)

    def test_admin_edit_election_legal_voters(self):
        """ Test the admin_edit_election function when editing legal voters.
        """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/edit')
            self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election3/edit')
            self.assertEqual(output.status_code, 200)
            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]
            # Edit LegalVoter Group

            # Check election before edit
            output = self.app.get('/admin/test_election3/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<li>Number elected: 1</li>' in output.data)
            self.assertTrue('<li>Admin groups: </li>' in output.data)
            self.assertTrue('<li>Legal voters: voters</li>' in output.data)

            # Add a new admin group: sysadmin-main
            data = {
                'alias': 'test_election3',
                'shortdesc': 'test election 3 shortdesc',
                'description': 'test election 3 description',
                'voting_type': 'range',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY - timedelta(days=2),
                'end_date': TODAY + timedelta(days=3),
                'seats_elected': '1',
                'candidates_are_fasusers': False,
                'embargoed': False,
                'lgl_voters': 'voters, sysadmin-main',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election3/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Election "test_election3" saved</li>'
                in output.data)
            # We edited the legal_voters
            self.assertTrue(
                '<li>Legal voters: sysadmin-main, voters</li>'
                in output.data)

            # Remove an existing group: voters
            data = {
                'alias': 'test_election3',
                'shortdesc': 'test election 3 shortdesc',
                'description': 'test election 3 description',
                'voting_type': 'range',
                'url': 'https://fedoraproject.org',
                'start_date': TODAY - timedelta(days=2),
                'end_date': TODAY + timedelta(days=3),
                'seats_elected': '1',
                'candidates_are_fasusers': False,
                'embargoed': False,
                'lgl_voters': 'sysadmin-main',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election3/edit', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Election "test_election3" saved</li>'
                in output.data)
            # We edited the legal_voters
            self.assertTrue(
                '<li>Legal voters: sysadmin-main</li>'
                in output.data)

    def test_admin_add_candidate(self):
        """ Test the admin_add_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/new')
            self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/new')
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h2>Add candidate</h2>' in output.data)
            self.assertTrue(
                'input id="name" name="name" type="text"' in output.data)

            data = {
                'name': 'pingou',
                'url': '',
            }

            output = self.app.post(
                '/admin/test_election/candidates/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Add candidate</h2>' in output.data)
            self.assertTrue(
                'input id="name" name="name" type="text"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'name': '',
                'url': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/candidates/new', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Add candidate</h2>' in output.data)
            self.assertTrue(
                'input id="name" name="name" type="text"' in output.data)
            self.assertTrue(
                '<td class="error">This field is required.</td>'
                in output.data)

            data = {
                'name': 'pingou',
                'url': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/candidates/new', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Candidate "pingou" saved</li>'
                in output.data)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<p>4 candidates found</p>' in output.data)

    def test_admin_add_multi_candidate(self):
        """ Test the admin_add_multi_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/new/multi')
            self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/new/multi')
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h2>Add candidates</h2>' in output.data)
            self.assertTrue(
                'input id="candidate" name="candidate" type="text"'
                in output.data)

            data = {
                'candidate': 'pingou',
            }

            output = self.app.post(
                '/admin/test_election/candidates/new/multi', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Add candidates</h2>' in output.data)
            self.assertTrue(
                'input id="candidate" name="candidate" type="text"'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'candidate': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/candidates/new/multi', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Add candidates</h2>' in output.data)
            self.assertTrue(
                'input id="candidate" name="candidate" type="text"'
                in output.data)
            self.assertTrue(
                '<td class="error">This field is required.</td>'
                in output.data)

            data = {
                'candidate': 'pingou|patrick!https://fedoraproject.org|'
                'shaiton!https://fedoraproject.org!test|sochotni',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/candidates/new/multi', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Added 3 candidates</li>'
                in output.data)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<p>6 candidates found</p>' in output.data)

    def test_admin_edit_candidate(self):
        """ Test the admin_edit_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')

        self.setup_db()

        # Election does not exist
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test/candidates/1/edit')
            self.assertEqual(output.status_code, 404)

        # Candidate does not exist
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/100/edit')
            self.assertEqual(output.status_code, 404)

        # Candidate not in election
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/5/edit')
            self.assertEqual(output.status_code, 404)

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/1/edit')
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h2>Edit candidate</h2>' in output.data)
            self.assertTrue(
                'input id="name" name="name" type="text"' in output.data)

            data = {
                'name': 'Toshio Kuratomi',
                'url': 'https://fedoraproject.org/wiki/User:Toshio',
            }

            self.assertTrue('<h2>Edit candidate</h2>' in output.data)
            self.assertTrue(
                'input id="name" name="name" type="text"' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            data = {
                'name': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/candidates/1/edit', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Edit candidate</h2>' in output.data)
            self.assertTrue(
                'input id="name" name="name" type="text"' in output.data)
            self.assertTrue(
                '<td class="error">This field is required.</td>'
                in output.data)

            # Check election before edit
            output = self.app.get('/admin/test_election/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<p>3 candidates found</p>' in output.data)
            self.assertTrue('<li>Number elected: 1</li>' in output.data)
            self.assertFalse('<li>Toshio Kuratomi' in output.data)

            data = {
                'name': 'Toshio Kuratomi',
                'url': 'https://fedoraproject.org/wiki/User:Toshio',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/candidates/1/edit', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Candidate "Toshio Kuratomi" saved</li>'
                in output.data)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<p>3 candidates found</p>' in output.data)
            self.assertTrue('<li>Toshio Kuratomi' in output.data)

    def test_admin_delete_candidate(self):
        """ Test the admin_delete_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')

        self.setup_db()

        # Election does not exist
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test/candidates/1/delete')
            self.assertEqual(output.status_code, 404)

        # Candidate does not exist
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/100/delete')
            self.assertEqual(output.status_code, 404)

        # Candidate not in election
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/5/delete')
            self.assertEqual(output.status_code, 404)

        with user_set(fedora_elections.APP, user):
            output = self.app.get('/admin/test_election/candidates/1/delete')
            self.assertEqual(output.status_code, 200)

            self.assertTrue('<h2>Delete candidate</h2>' in output.data)
            self.assertTrue(
                'p>Are you sure you want to delete candidate "Toshio"?</p'
                in output.data)

            output = self.app.post('/admin/test_election/candidates/1/delete')
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>Delete candidate</h2>' in output.data)
            self.assertTrue(
                'p>Are you sure you want to delete candidate "Toshio"?</p'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Try to delete while there are votes link to this candidates
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election/candidates/1/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<h2>test election shortdesc</h2>' in output.data)
            self.assertTrue(
                '<li class="error">Could not delete this candidate. Is it '
                'already part of an election?</li>' in output.data)

            # Check election before edit
            output = self.app.get('/admin/test_election4/')
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<p>2 candidates found</p>' in output.data)
            self.assertTrue('<li>Number elected: 1</li>' in output.data)
            self.assertTrue('<li>Toshio' in output.data)
            self.assertTrue(
                '<h2>test election 4 shortdesc</h2>' in output.data)

            # Delete one candidate
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/admin/test_election4/candidates/10/delete', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Candidate "Toshio" deleted</li>'
                in output.data)
            self.assertTrue(
                '<h2>test election 4 shortdesc</h2>' in output.data)
            self.assertTrue('<h3>Candidates</h3>' in output.data)
            self.assertTrue('<p>1 candidates found</p>' in output.data)
            self.assertFalse('<li>Toshio' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskAdmintests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
