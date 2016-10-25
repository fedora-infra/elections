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
                'You must sign the CLA to vote'
                in output.data)

        user = FakeUser([], username='pingou')
        with user_set(fedora_elections.APP, user):

            output = self.app.get('/vote/test_election')
            self.assertEqual(output.status_code, 302)

            output = self.app.get(
                '/vote/test_election', follow_redirects=True)
            self.assertTrue(
                'You need to be in one another group than '
                'CLA to vote' in output.data)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedora_elections.APP, user):

            output = self.app.get('/vote/test_election3')
            self.assertEqual(output.status_code, 302)

            # Election closed and results open
            output = self.app.get(
                '/vote/test_election3', follow_redirects=True)
            self.assertTrue(
                'You are not among the groups that are '
                'allowed to vote for this election' in output.data)

        user = FakeUser(['voters'], username='pingou')
        with user_set(fedora_elections.APP, user):

            output = self.app.get('/vote/test_election')
            self.assertEqual(output.status_code, 302)

            # Election closed and results open
            output = self.app.get(
                '/vote/test_election', follow_redirects=True)
            self.assertTrue(
                'This election is closed.  You have been '
                'redirected to the election results.' in output.data)

            # Election closed and results are embargoed
            output = self.app.get(
                '/vote/test_election2', follow_redirects=True)
            self.assertTrue(
                'This election is closed.  You have been '
                'redirected to the election results.' in output.data)

            # Election still pending
            output = self.app.get(
                '/vote/test_election4', follow_redirects=True)
            self.assertTrue(
                'Voting has not yet started, sorry.'
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
            'We are sorry.  The results for this '
            'election cannot be viewed because they are currently embargoed '
            'pending formal announcement.' in output.data)
        self.assertTrue('<h3>Current elections</h3>' in output.data)

        user = FakeUser(['packager'], username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/results/test_election2', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'We are sorry.  The results for this '
                'election cannot be viewed because they are currently '
                'embargoed pending formal announcement.'
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
                'You are only seeing this page because '
                'you are an admin.' in output.data)
            self.assertTrue(
                ' The results for this election are '
                'currently embargoed pending formal announcement.'
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
                'Sorry but this election is in progress,'
                ' and you may not see its results yet.' in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)

    def test_election_results_text(self):
        """ Test the election_results_text function - the preview part. """
        output = self.app.get(
            '/results/test_election/text', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            'class="message">The election, test_election, does not exist.</'
            in output.data)

        self.setup_db()

        output = self.app.get(
            '/results/test_election/text', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            'class="error">The text results are only available to the '
            'admins</li>' in output.data)
        self.assertTrue('<h2>Elections</h2>' in output.data)

        user = FakeUser(['packager'], username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/results/test_election2/text', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="error">The text results are only available to the '
                'admins</li>' in output.data)
            self.assertTrue('<h2>Elections</h2>' in output.data)

        user = FakeUser(
            fedora_elections.APP.config['FEDORA_ELECTIONS_ADMIN_GROUP'],
            username='toshio')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/results/test_election/text', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            exp = """<!DOCTYPE html>

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <title>Fedora elections</title>
    <link rel="shortcut icon" type="image/vnd.microsoft.icon"
        href="//fedoraproject.org/static/images/favicon.ico"/>
  </head>
  <body>
<pre>
Greetings, all!

The elections for test election shortdesc have concluded, and the results
are shown below.

XXX is electing 1 seats this time.
A total of 2 ballots were cast, meaning a candidate
could accumulate up to 6 votes (2 * 3).

The results for the elections are as follows:

  # votes |  name
- --------+----------------------
       8  | Kevin
- --------+----------------------
       7  | Ralph
       6  | Toshio


Congratulations to the winning candidates, and thank you all
candidates for running this elections!
</pre>

</body>
</html>"""
            self.assertEqual(output.data, exp)

            output = self.app.get(
                '/results/test_election2/text', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            exp = """<!DOCTYPE html>

<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <title>Fedora elections</title>
    <link rel="shortcut icon" type="image/vnd.microsoft.icon"
        href="//fedoraproject.org/static/images/favicon.ico"/>
  </head>
  <body>
<pre>
Greetings, all!

The elections for test election 2 shortdesc have concluded, and the results
are shown below.

XXX is electing 1 seats this time.
A total of 0 ballots were cast, meaning a candidate
could accumulate up to 0 votes (0 * 0).

The results for the elections are as follows:

  # votes |  name
- --------+----------------------


Congratulations to the winning candidates, and thank you all
candidates for running this elections!
</pre>

</body>
</html>"""

            self.assertEqual(output.data, exp)

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedora_elections.APP, user):
            output = self.app.get(
                '/results/test_election3/text', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'Sorry but this election is in progress,'
                ' and you may not see its results yet.' in output.data)
            self.assertTrue('<h3>Current elections</h3>' in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskElectionstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
