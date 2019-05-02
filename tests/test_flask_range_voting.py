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
from mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedora_elections
from tests import ModelFlasktests, Modeltests, TODAY, FakeUser, user_set


# pylint: disable=R0904
class FlaskRangeElectionstests(ModelFlasktests):
    """ Flask application tests range voting. """

    def test_vote_range(self):
        """ Test the vote_range function - the preview part. """
        output = self.app.get('/vote/test_election')
        self.assertEqual(output.status_code, 302)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '/login?next=http%3A%2F%2Flocalhost%2Fvote%2Ftest_election',
            output_text)

        self.setup_db()

        user = FakeUser(['voters'], username='pingou')
        with user_set(fedora_elections.APP, user, oidc_id_token='foobar'):
            with patch(
                    'fedora_elections.OIDC.user_getfield',
                    MagicMock(return_value=['voters'])):
                output = self.app.get('/vote/test_election3')
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'test election 3 shortdesc' in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text)

                # Invalid candidate id
                data = {
                    'Toshio': 1,
                    'kevin': 3,
                    'Ralph': 2,
                    'action': 'preview',
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    3)

                csrf_token = output_text.split(
                    'name="csrf_token" type="hidden" value="')[1].split('">')[0]

                # Invalid candidate id
                data = {
                    'Toshio': 1,
                    'Kevin': 3,
                    'Ralph': 2,
                    'action': 'preview',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    3)

                # Invalid vote: too low
                data = {
                    '9': -1,
                    '6': 0,
                    '5': 2,
                    'action': 'preview',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'test election 3 shortdesc' in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    1)

                # Invalid vote: 2 are too high
                data = {
                    '9': 5,
                    '6': 3,
                    '5': 2,
                    'action': 'preview',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'test election 3 shortdesc' in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    2)

                # Invalid vote: Not numeric
                data = {
                    '9': 'a',
                    '6': 0,
                    '5': 2,
                    'action': 'preview',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'test election 3 shortdesc' in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    1)

                # Valid input
                data = {
                    '4': 1,
                    '6': 0,
                    '5': 2,
                    'action': 'preview',
                    'csrf_token': csrf_token,
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'test election 3 shortdesc' in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="submit" />'
                    in output_text)

    def test_vote_range_process(self):
        """ Test the vote_range function - the voting part. """
        output = self.app.get('/vote/test_election')
        self.assertEqual(output.status_code, 302)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '/login?next=http%3A%2F%2Flocalhost%2Fvote%2Ftest_election',
            output_text)

        self.setup_db()

        user = FakeUser(['voters'], username='pingou')
        with user_set(fedora_elections.APP, user, oidc_id_token='foobar'):
            with patch(
                    'fedora_elections.OIDC.user_getfield',
                    MagicMock(return_value=['voters'])):
                # No csrf token provided
                data = {
                    'Toshio': 1,
                    'Kevin': 3,
                    'Ralph': 2,
                    'action': 'submit',
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    3)

                csrf_token = output_text.split(
                    'name="csrf_token" type="hidden" value="')[1].split('">')[0]

                # Invalid vote: invalid username
                data = {
                    'Toshio': 1,
                    'Kevin': 3,
                    'Ralph': 2,
                    'action': 'submit',
                }

                output = self.app.post('/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    3)

                # Invalid vote: too low
                data = {
                    '4': -1,
                    '5': 0,
                    '6': 2,
                    'action': 'submit',
                    'csrf_token': csrf_token,
                }

                output = self.app.post(
                    '/vote/test_election3', data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    1)

                # Invalid vote: 2 are too high
                data = {
                    '4': 5,
                    '5': 3,
                    '6': 2,
                    'action': 'submit',
                    'csrf_token': csrf_token,
                }

                output = self.app.post(
                    '/vote/test_election3', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    2)

                # Invalid vote: Not numeric
                data = {
                    '4': 'a',
                    '5': 0,
                    '6': 2,
                    'action': 'submit',
                    'csrf_token': csrf_token,
                }

                output = self.app.post(
                    '/vote/test_election3', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertEqual(
                    output_text.count('<div class="form-control-feedback">Not a valid choice</div>'),
                    1)

                # Valid input
                data = {
                    '4': 1,
                    '5': 0,
                    '6': 2,
                    'action': 'submit',
                    'csrf_token': csrf_token,
                }

                output = self.app.post(
                    '/vote/test_election3', data=data, follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'Your vote has been recorded.  Thank you!'
                    in output_text)
                self.assertTrue('Open elections' in output_text)

    def test_vote_range_revote(self):
        """ Test the vote_range function - the re-voting part. """
        #First we need to vote
        self.setup_db()

        user = FakeUser(['voters'], username='nerdsville')
        with user_set(fedora_elections.APP, user, oidc_id_token='foobar'):
            with patch(
                    'fedora_elections.OIDC.user_getfield',
                    MagicMock(return_value=['voters'])):
                retrieve_csrf = self.app.post('/vote/test_election3')
                csrf_token = retrieve_csrf.get_data(as_text=True).split(
                    'name="csrf_token" type="hidden" value="')[1].split('">')[0]
                data = {
                    '4': 1,
                    '5': 0,
                    '6': 2,
                    'action': 'submit',
                    'csrf_token': csrf_token,
                }
                self.app.post('/vote/test_election3', data=data, follow_redirects=True)
                vote = fedora_elections.models.Vote
                votes = vote.of_user_on_election(self.session, "nerdsville", '3')
                self.assertEqual(votes[0].value, 1)
                self.assertEqual(votes[1].value, 0)
                self.assertEqual(votes[2].value, 2)
            #Let's not do repetition of what is tested above we aren't testing the
            #functionality of voting as that has already been asserted

                obj = fedora_elections.models.Candidate(  # id:16
                    election_id=3,
                    name='Josh',
                    url='https://fedoraproject.org/wiki/User:Nerdsville',
                )
                self.session.add(obj)
                self.session.commit()


            #Next, we need to try revoting
                newdata = {
                    '4': 2,
                    '5': 1,
                    '6': 1,
                    '16': 0,
                    'action': 'submit',
                    'csrf_token': csrf_token,
                }
                output = self.app.post('/vote/test_election3', data=newdata, follow_redirects=True)
            #Next, we need to check if the vote has been recorded
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'Your vote has been recorded.  Thank you!'
                    in output_text)
                self.assertTrue('Open elections' in output_text)
                vote = fedora_elections.models.Vote
                votes = vote.of_user_on_election(self.session, "nerdsville", '3')
                self.assertEqual(votes[0].value, 2)
                self.assertEqual(votes[1].value, 1)
                self.assertEqual(votes[2].value, 1)
                self.assertEqual(votes[3].value, 0)
            #If we haven't failed yet, HOORAY!


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(
        FlaskRangeElectionstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
