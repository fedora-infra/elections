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
__requires__ = ["SQLAlchemy >= 0.7", "jinja2 >= 2.4"]
import pkg_resources

import logging
import unittest
import sys
import os

from datetime import time
from datetime import timedelta

import flask
from mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import fedora_elections
from tests import ModelFlasktests, Modeltests, TODAY, FakeUser, user_set


# pylint: disable=R0904
class FlaskElectionstests(ModelFlasktests):
    """ Flask application tests for the elections controller. """

    def test_vote_empty(self):
        """ Test the vote function without data. """
        output = self.app.get("/vote/test_election")
        self.assertEqual(output.status_code, 302)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            "/login?next=http%3A%2F%2Flocalhost%2Fvote%2Ftest_election", output_text
        )

        user = FakeUser(["packager"], username="pingou")
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["packager"]),
            ):
                output = self.app.get("/vote/test_election")
                self.assertEqual(output.status_code, 302)

                output = self.app.get("/vote/test_election", follow_redirects=True)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    "The election, test_election, does not exist." in output_text
                )

    def test_vote(self):
        """ Test the vote function. """
        output = self.app.get("/vote/test_election")
        self.assertEqual(output.status_code, 302)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            "/login?next=http%3A%2F%2Flocalhost%2Fvote%2Ftest_election", output_text
        )

        self.setup_db()

        user = FakeUser([], username="pingou", cla_done=False)
        with user_set(fedora_elections.APP, user):

            output = self.app.get("/vote/test_election")
            self.assertEqual(output.status_code, 302)

            output = self.app.get("/vote/test_election", follow_redirects=True)
            output_text = output.get_data(as_text=True)
            self.assertTrue("You must sign the CLA to vote" in output_text)

        user = FakeUser([], username="pingou")
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield", MagicMock(return_value=[])
            ):

                output = self.app.get("/vote/test_election")
                self.assertEqual(output.status_code, 302)

                output = self.app.get("/vote/test_election", follow_redirects=True)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    "You need to be in one another group than "
                    "CLA to vote" in output_text
                )

        user = FakeUser(["packager"], username="pingou")
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["packager"]),
            ):

                output = self.app.get("/vote/test_election3")
                self.assertEqual(output.status_code, 302)

                # Election closed and results open
                output = self.app.get("/vote/test_election3", follow_redirects=True)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    "You are not among the groups that are "
                    "allowed to vote for this election" in output_text
                )

        user = FakeUser(["voters"], username="pingou")
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["voters"]),
            ):

                output = self.app.get("/vote/test_election")
                self.assertEqual(output.status_code, 302)

                # Election closed and results open
                output = self.app.get("/vote/test_election", follow_redirects=True)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    '<span class="label label-danger">Election Closed</span>'
                    in output_text
                )

                # Election closed and results are embargoed
                output = self.app.get("/vote/test_election2", follow_redirects=True)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    '<span class="label label-danger">Election Closed</span>'
                    in output_text
                )

                # Election still pending
                output = self.app.get("/vote/test_election4", follow_redirects=True)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Voting has not yet started, sorry." in output_text)

                # Election in progress
                output = self.app.get("/vote/test_election3")
                output_text = output.get_data(as_text=True)
                self.assertTrue("test election 3 shortdesc" in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text
                )

                # Election in progress
                output = self.app.get("/vote/test_election5")
                output_text = output.get_data(as_text=True)
                self.assertTrue("test election 5 shortdesc" in output_text)
                self.assertTrue(
                    '<input type="hidden" name="action" value="preview" />'
                    in output_text
                )

    def test_election_results(self):
        """ Test the election_results function - the preview part. """
        output = self.app.get("/about/test_election", follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertTrue("The election, test_election,  does not exist." in output_text)

        self.setup_db()

        output = self.app.get("/about/test_election")
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertTrue(
            '<th class="nowrap" title="Number of votes received">Votes</th>'
            in output_text
        )
        self.assertTrue("<h3>Some statistics about this election</h3>" in output_text)

        output = self.app.get("/about/test_election2", follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertTrue(
            "The results for this election cannot be viewed because they are "
            in output_text
        )

        user = FakeUser(["packager"], username="toshio")
        with user_set(fedora_elections.APP, user):
            output = self.app.get("/about/test_election2", follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertTrue(
                "The results for this election cannot be viewed because they are "
                in output_text
            )

        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/about/test_election2", follow_redirects=True)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    "You are only seeing these results because you are an admin."
                    in output_text
                )
                self.assertTrue(
                    "The results for this election are currently embargoed "
                    in output_text
                )
                self.assertTrue(
                    '<th class="nowrap" title="Number of votes received">Votes</th>'
                    in output_text
                )
                self.assertTrue(
                    "<h3>Some statistics about this election</h3>" in output_text
                )

        user = FakeUser(["gitr2spec"], username="kevin")
        with user_set(fedora_elections.APP, user):
            output = self.app.get("/about/test_election3", follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertTrue(
                '<span class="label label-success">Election Open</span>' in output_text
            )

    def test_election_results_text(self):
        """ Test the election_results_text function - the preview part. """
        output = self.app.get("/results/test_election/text", follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertTrue("The election, test_election, does not exist." in output_text)

        self.setup_db()

        output = self.app.get("/results/test_election/text", follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertTrue(
            "The text results are only available to the " "admins" in output_text
        )

        user = FakeUser(["packager"], username="toshio")
        with user_set(fedora_elections.APP, user):
            output = self.app.get("/results/test_election2/text", follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertTrue(
                "The text results are only available to the " "admins" in output_text
            )
            self.assertTrue("<h2>Elections" in output_text)

        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get(
                    "/results/test_election/text", follow_redirects=True
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
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
                print(output_text)
                self.assertEqual(output_text, exp)

                output = self.app.get(
                    "/results/test_election2/text", follow_redirects=True
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
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

                self.assertEqual(output_text, exp)

        user = FakeUser(["gitr2spec"], username="kevin")
        with user_set(fedora_elections.APP, user):
            output = self.app.get("/results/test_election3/text", follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertTrue(
                "Sorry but this election is in progress,"
                " and you may not see its results yet." in output_text
            )
            self.assertTrue("Open elections" in output_text)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskElectionstests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
