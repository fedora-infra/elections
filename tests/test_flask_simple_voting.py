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

import os
import sys
import unittest

from mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import fedora_elections  # noqa:E402
from tests import ModelFlasktests, FakeUser, user_set  # noqa:E402


# pylint: disable=R0904
class FlaskSimpleElectionstests(ModelFlasktests):
    """ Flask application tests range voting. """

    def test_vote_simple(self):
        """ Test the vote_simple function - the preview part. """
        output = self.app.get("/vote/test_election")
        self.assertEqual(output.status_code, 302)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            "/login?next=http%3A%2F%2Flocalhost%2Fvote%2Ftest_election", output_text
        )

        self.setup_db()

        user = FakeUser(["packager"], username="pingou")
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["voters"]),
            ):
                output = self.app.get("/vote/test_election5")
                output_text = output.get_data(as_text=True)
                self.assertTrue("test election 5 shortdesc" in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text
                )

                # Invalid vote: No candidate
                data = {
                    "action": "preview",
                }

                output = self.app.post("/vote/test_election5", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("test election 5 shortdesc" in output_text)
                self.assertTrue("Preview your vote" in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text
                )

                csrf_token = output_text.split(
                    'name="csrf_token" type="hidden" value="'
                )[1].split('">')[0]

                # Invalid vote: No candidate
                data = {
                    "action": "preview",
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/vote/test_election5", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("test election 5 shortdesc" in output_text)
                self.assertTrue("Preview your vote" in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text
                )

                # Invalid vote: Not numeric
                data = {
                    "candidate": "a",
                    "action": "preview",
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/vote/test_election5", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("test election 5 shortdesc" in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text
                )

                # Valid input
                data = {
                    "candidate": 7,
                    "action": "preview",
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/vote/test_election5", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("test election 5 shortdesc" in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="submit" />'
                    in output_text
                )
                self.assertTrue("Please confirm your vote!" in output_text)

    def test_vote_simple_process(self):
        """ Test the vote_simple function - the voting part. """
        output = self.app.get("/vote/test_election")
        self.assertEqual(output.status_code, 302)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            "/login?next=http%3A%2F%2Flocalhost%2Fvote%2Ftest_election", output_text
        )

        self.setup_db()

        user = FakeUser(["packager"], username="pingou")
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["voters"]),
            ):
                # Invalid candidate id - no csrf
                data = {
                    "candidate": 1,
                    "action": "submit",
                }

                output = self.app.post(
                    "/vote/test_election5", data=data, follow_redirects=True
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                csrf_token = output_text.split(
                    'name="csrf_token" type="hidden" value="'
                )[1].split('">')[0]

                # Invalid candidate id
                data = {
                    "candidate": 1,
                    "action": "submit",
                    "csrf_token": csrf_token,
                }

                output = self.app.post(
                    "/vote/test_election5", data=data, follow_redirects=True
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                # Invalid vote: too low
                data = {
                    "candidate": -1,
                    "action": "submit",
                    "csrf_token": csrf_token,
                }

                output = self.app.post(
                    "/vote/test_election5", data=data, follow_redirects=True
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                # Invalid vote: Not numeric
                data = {
                    "candidate": "a",
                    "action": "submit",
                    "csrf_token": csrf_token,
                }

                output = self.app.post(
                    "/vote/test_election5", data=data, follow_redirects=True
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                # Valid input
                data = {
                    "candidate": 8,
                    "action": "submit",
                    "csrf_token": csrf_token,
                }

                output = self.app.post(
                    "/vote/test_election5", data=data, follow_redirects=True
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    "Your vote has been recorded.  Thank you!" in output_text
                )
                self.assertTrue("Open elections" in output_text)

    def test_vote_simple_revote(self):
        """ Test the vote_simple function - the re-voting part. """
        # First we need to vote
        self.setup_db()

        user = FakeUser(["voters"], username="nerdsville")
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["voters"]),
            ):
                retrieve_csrf = self.app.post("/vote/test_election5")
                csrf_token = (
                    retrieve_csrf.get_data(as_text=True)
                    .split('name="csrf_token" type="hidden" value="')[1]
                    .split('">')[0]
                )
                # Valid input
                data = {
                    "candidate": 8,
                    "action": "submit",
                    "csrf_token": csrf_token,
                }

                self.app.post("/vote/test_election5", data=data, follow_redirects=True)
                vote = fedora_elections.models.Vote
                votes = vote.of_user_on_election(self.session, "nerdsville", "5")
                self.assertEqual(votes[0].candidate_id, 8)
                # Let's not do repetition of what is tested above we aren't testing the
                # functionality of voting as that has already been asserted

                # Next, we need to try revoting
                # Valid input
                newdata = {
                    "candidate": 9,
                    "action": "submit",
                    "csrf_token": csrf_token,
                }
                output = self.app.post(
                    "/vote/test_election5", data=newdata, follow_redirects=True
                )
                # Next, we need to check if the vote has been recorded
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    "Your vote has been recorded.  Thank you!" in output_text
                )
                self.assertTrue("Open elections" in output_text)
                vote = fedora_elections.models.Vote
                votes = vote.of_user_on_election(self.session, "nerdsville", "5")
                self.assertEqual(votes[0].candidate_id, 9)

            # If we haven't failed yet, HOORAY!


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskSimpleElectionstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
