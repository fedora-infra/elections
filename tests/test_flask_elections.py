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

 fedora_elections.elections test script
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
class FlaskElectionstests(ModelFlasktests):
    """ Flask application tests for the elections controller. """

    def test_vote_empty(self):
        """ Test the vote function without data. """
        output = self.app.get('/vote/test_election')
        self.assertEqual(output.status_code, 302)

        output = self.app.get('/vote/test_election', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data
            or 'discoveryfailure' in output.data)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get('/vote/test_election')
            self.assertEqual(output.status_code, 302)

            output = self.app.get('/vote/test_election', follow_redirects=True)
            self.assertTrue(
                '"message">The election, test_election, does not exist.</'
                in output.data)

    def test_vote(self):
        """ Test the vote function. """
        output = self.app.get('/vote/test_election', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data
            or 'discoveryfailure' in output.data)

        self.setup_db()

        user = FakeUser([], username='pingou', cla_done=False)
        with user_set(fedora_elections.APP, user):

            output = self.app.get('/vote/test_election')
            self.assertEqual(output.status_code, 302)

            output = self.app.get(
                '/vote/test_election', follow_redirects=True)
            self.assertTrue(
                '<li class="error">You must sign the CLA to vote</li>'
                in output.data)

        user = FakeUser([], username='pingou')
        with user_set(fedora_elections.APP, user):

            output = self.app.get('/vote/test_election')
            self.assertEqual(output.status_code, 302)

            output = self.app.get(
                '/vote/test_election', follow_redirects=True)
            self.assertTrue(
                '<li class="error">You need to be in one another group than '
                'CLA to vote</li>' in output.data)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedora_elections.APP, user):

            output = self.app.get('/vote/test_election3')
            self.assertEqual(output.status_code, 302)

            # Election closed and results open
            output = self.app.get(
                '/vote/test_election3', follow_redirects=True)
            self.assertTrue(
                '<li class="error">You are not among the groups that are '
                'allowed to vote for this election</li>' in output.data)

        user = FakeUser(['voters'], username='pingou')
        with user_set(fedora_elections.APP, user):

            output = self.app.get('/vote/test_election')
            self.assertEqual(output.status_code, 302)

            # Election closed and results open
            output = self.app.get(
                '/vote/test_election', follow_redirects=True)
            self.assertTrue(
                '<li class="message">This election is closed.  You have been '
                'redirected to the election results.</li>' in output.data)

            # Election closed and results are embargoed
            output = self.app.get(
                '/vote/test_election2', follow_redirects=True)
            self.assertTrue(
                '<li class="message">This election is closed.  You have been '
                'redirected to the election results.</li>' in output.data)

            # Election still pending
            output = self.app.get(
                '/vote/test_election4', follow_redirects=True)
            self.assertTrue(
                '<li class="message">Voting has not yet started, sorry.</li>'
                in output.data)

            # Election in progress
            output = self.app.get('/vote/test_election3')
            self.assertTrue(
                '<h2>test election 3 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)

            # Election in progress
            output = self.app.get('/vote/test_election5')
            self.assertTrue(
                '<h2>test election 5 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)

        user = FakeUser(['voters'], username='toshio')
        with user_set(fedora_elections.APP, user):

            # Election in progress
            output = self.app.get(
                '/vote/test_election3', follow_redirects=True)
            self.assertTrue(
                'class="message">You have already voted in the election!</'
                in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)

    def test_vote_range(self):
        """ Test the vote_range function - the preview part. """
        output = self.app.get(
            '/vote/test_election', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data
            or 'discoveryfailure' in output.data)

        self.setup_db()

        user = FakeUser(['voters'], username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/vote/test_election3', follow_redirects=True)
            self.assertTrue(
                'class="message">You have already voted in the election!</'
                in output.data)

        user = FakeUser(['voters'], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/vote/test_election3')
            self.assertTrue(
                '<h2>test election 3 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)

            # Invalid candidate id
            data = {
                '9': 1,
                '5': 3,
                '6': 2,
                'action': 'preview',
            }

            output = self.app.post('/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                3)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Invalid candidate id
            data = {
                '9': 1,
                '5': 3,
                '6': 2,
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                3)

            # Invalid vote: too low
            data = {
                'Toshio': -1,
                'Kevin': 3,
                'Ralph': 2,
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 3 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Invalid vote: too high
            data = {
                'Toshio': 5,
                'Kevin': 3,
                'Ralph': 2,
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 3 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Invalid vote: Not numeric
            data = {
                'Toshio': 'a',
                'Kevin': 3,
                'Ralph': 2,
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 3 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Valid input
            data = {
                'Toshio': 1,
                'Kevin': 3,
                'Ralph': 2,
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 3 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="submit" />'
                in output.data)
            self.assertTrue('<div class="vtmedcool">' in output.data)
            self.assertTrue('<div class="vthot">' in output.data)
            self.assertTrue('<div class="vtmedwarm">' in output.data)

    def test_vote_range_process(self):
        """ Test the vote_range function - the voting part. """
        output = self.app.get(
            '/vote/test_election', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data
            or 'discoveryfailure' in output.data)

        self.setup_db()

        user = FakeUser(['voters'], username='pingou')
        with user_set(fedora_elections.APP, user):
            # No csrf token provided
            data = {
                '9': 1,
                '5': 3,
                '6': 2,
                'action': 'submit',
            }

            output = self.app.post('/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                3)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Invalid vote: too low
            data = {
                'Toshio': -1,
                'Kevin': 3,
                'Ralph': 2,
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election3', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Invalid vote: too high
            data = {
                'Toshio': 5,
                'Kevin': 3,
                'Ralph': 2,
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election3', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Invalid vote: Not numeric
            data = {
                'Toshio': 'a',
                'Kevin': 3,
                'Ralph': 2,
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election3', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Valid input
            data = {
                'Toshio': 1,
                'Kevin': 3,
                'Ralph': 2,
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election3', data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="message">Your vote has been recorded.  Thank you!</'
                in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)
            self.assertTrue('<h3>Next 1 elections</h3>' in output.data)
            self.assertTrue('<h3>Last 2 elections</h3>' in output.data)

    def test_vote_simple(self):
        """ Test the vote_simple function - the preview part. """
        output = self.app.get(
            '/vote/test_election', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data
            or 'discoveryfailure' in output.data)

        self.setup_db()

        user = FakeUser(['packager'], username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/vote/test_election5', follow_redirects=True)
            self.assertTrue(
                'class="message">You have already voted in the election!</'
                in output.data)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/vote/test_election5')
            self.assertTrue(
                '<h2>test election 5 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)

            # Invalid vote: No candidate
            data = {
                'action': 'preview',
            }

            output = self.app.post('/vote/test_election5', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 5 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<td class="error">Not a valid choice</td>'
                in output.data)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Invalid vote: No candidate
            data = {
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election5', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 5 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<td class="error">Not a valid choice</td>'
                in output.data)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)

            # Invalid vote: Not numeric
            data = {
                'candidate': 'a',
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election5', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 5 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="preview" />'
                in output.data)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Valid input
            data = {
                'candidate': 7,
                'action': 'preview',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/vote/test_election5', data=data)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<h2>test election 5 shortdesc</h2>' in output.data)
            self.assertTrue(
                '<input type="hidden" name="action" value="submit" />'
                in output.data)
            self.assertTrue(
                '<li class="message">Please confirm your vote!</li>'
                in output.data)

    def test_vote_simple_process(self):
        """ Test the vote_simple function - the voting part. """
        output = self.app.get(
            '/vote/test_election', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>OpenID transaction in progress</title>' in output.data
            or 'discoveryfailure' in output.data)

        self.setup_db()

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedora_elections.APP, user):
            # Invalid candidate id - no csrf
            data = {
                'candidate': 1,
                'action': 'submit',
            }

            output = self.app.post(
                '/vote/test_election5', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Invalid candidate id
            data = {
                'candidate': 1,
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election5', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Invalid vote: too low
            data = {
                'candidate': -1,
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election5', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Invalid vote: Not numeric
            data = {
                'candidate': 'a',
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election5', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td class="error">Not a valid choice</td>'),
                1)

            # Valid input
            data = {
                'candidate': 8,
                'action': 'submit',
                'csrf_token': csrf_token,
            }

            output = self.app.post(
                '/vote/test_election5', data=data,
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="message">Your vote has been recorded.  Thank you!</'
                in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)
            self.assertTrue('<h3>Next 1 elections</h3>' in output.data)
            self.assertTrue('<h3>Last 2 elections</h3>' in output.data)

    def test_election_results(self):
        """ Test the election_results function - the preview part. """
        output = self.app.get(
            '/results/test_election', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            'class="message">The election, test_election, does not exist.</'
            in output.data)

        self.setup_db()

        output = self.app.get('/results/test_election')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<th title="Number of votes received">Votes</th>'
            in output.data)
        self.assertTrue(
            '<h3>Some statistics about this election</h3>'
            in output.data)

        output = self.app.get(
            '/results/test_election2', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<li class="message">We are sorry.  The results for this '
            'election cannot be viewed because they are currently embargoed '
            'pending formal announcement.</li>' in output.data)
        self.assertTrue('<h3>Current elections</h3>' in output.data)

        user = FakeUser(['packager'], username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/results/test_election2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">We are sorry.  The results for this '
                'election cannot be viewed because they are currently '
                'embargoed pending formal announcement.</li>'
                in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)

        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/results/test_election2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="warning">You are only seeing this page because '
                'you are an admin.</li>' in output.data)
            self.assertTrue(
                ' <li class="warning">The results for this election are '
                'currently embargoed pending formal announcement.</li>'
                in output.data)
            self.assertTrue(
                '<th title="Number of votes received">Votes</th>'
                in output.data)
            self.assertTrue(
                '<h3>Some statistics about this election</h3>'
                in output.data)

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/results/test_election3', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="message">Sorry but this election is in progress,'
                ' and you may not see its results yet.</li>' in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskElectionstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
