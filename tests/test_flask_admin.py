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
from fedora_messaging.testing import mock_sends
from fedora_elections_messages import (
    NewElectionV1,
    EditElectionV1,
    NewCandidateV1,
    EditCandidateV1,
    DeleteCandidateV1,
)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import fedora_elections
from tests import ModelFlasktests, Modeltests, TODAY, FakeUser, user_set


# pylint: disable=R0904
class FlaskAdmintests(ModelFlasktests):
    """ Flask application tests for the admin controller. """

    def test_admin_view_election(self):
        """ Test the admin_view_election function. """
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/election_test/")
                self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/")
                output_text = output.get_data(as_text=True)
                self.assertEqual(output.status_code, 200)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">3</span>'
                    in output_text
                )

    def test_admin_no_cla(self):
        """ Test the admin_new_election function. """
        self.setup_db()

        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        user.cla_done = False
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/new")
                self.assertEqual(output.status_code, 403)

    def test_admin_new_election(self):
        """ Test the admin_new_election function. """
        self.setup_db()

        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/new")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Create new election</h2>" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )

                # No csrf provided
                data = {
                    "alias": "new_election",
                    "shortdesc": "new election shortdesc",
                    "description": "new election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=2),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": "2",
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                }

                output = self.app.post("/admin/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Create new election</h2>" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )

                csrf_token = self.get_csrf(output=output)

                # Description missing
                data = {
                    "alias": "new_election",
                    "shortdesc": "new election shortdesc",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=2),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": "2",
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/admin/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Create new election</h2>" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )
                self.assertTrue(
                    '<div class="form-control-feedback">This field is required.</div>'
                    in output_text
                )

                # Invalid alias
                data = {
                    "alias": "new",
                    "shortdesc": "new election shortdesc",
                    "description": "new election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=2),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": 2,
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/admin/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Create new election</h2>" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )
                self.assertTrue(
                    '<div class="form-control-feedback">The alias cannot be <code>new</code>.</div>'
                    in output_text
                )

                # Invalid: end_date earlier than start_date
                data = {
                    "alias": "new_election",
                    "shortdesc": "new election shortdesc",
                    "description": "new election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=6),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": 2,
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/admin/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Create new election</h2>" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )
                self.assertTrue(
                    'class="form-control-feedback">End date must be later than start date.</div>'
                    in output_text
                )

                # Invalid: alias already taken
                data = {
                    "alias": "test_election",
                    "shortdesc": "new election shortdesc",
                    "description": "new election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=6),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": 2,
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/admin/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Create new election</h2>" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )
                self.assertTrue(
                    '<div class="form-control-feedback">There is already another election with '
                    "this alias.</div>" in output_text
                )

                # Invalid: shortdesc already taken
                data = {
                    "alias": "new_election",
                    "shortdesc": "test election shortdesc",
                    "description": "new election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=6),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": 2,
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/admin/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Create new election</h2>" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )
                self.assertTrue(
                    '<div class="form-control-feedback">There is already another election with '
                    "this summary.</div>" in output_text
                )

                # All good  -  max_votes is ignored as it is not a integer
                data = {
                    "alias": "new_election",
                    "shortdesc": "new election shortdesc",
                    "description": "new election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=2),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": 2,
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                    "admin_grp": "testers, sysadmin-main,,",
                    "lgl_voters": "testers, packager,,",
                    "max_votes": "wrong",
                    "csrf_token": csrf_token,
                }

                with mock_sends(NewElectionV1):
                    output = self.app.post(
                        "/admin/new", data=data, follow_redirects=True
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Election "new_election" added' in output_text)
                self.assertTrue("There are no candidates." in output_text)
                self.assertIn(
                    'input class="form-control" id="admin_grp" '
                    'name="admin_grp" type="text" '
                    'value="sysadmin-main, testers">',
                    output_text,
                )
                self.assertIn(
                    'input class="form-control" id="lgl_voters" '
                    'name="lgl_voters" type="text" '
                    'value="packager, testers">',
                    output_text,
                )
                self.assertIn(
                    'input class="form-control" id="max_votes" '
                    'name="max_votes" type="text" '
                    'value="">',
                    output_text,
                )

                # All good  -  max_votes is ignored as it is not a integer
                data = {
                    "alias": "new_election2",
                    "shortdesc": "new election2 shortdesc",
                    "description": "new election2 description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY + timedelta(days=2),
                    "end_date": TODAY + timedelta(days=4),
                    "seats_elected": 2,
                    "candidates_are_fasusers": False,
                    "embargoed": True,
                    "admin_grp": "testers, , sysadmin-main,,",
                    "lgl_voters": "testers, packager,,,",
                    "csrf_token": csrf_token,
                }

                with mock_sends(NewElectionV1):
                    output = self.app.post(
                        "/admin/new", data=data, follow_redirects=True
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Election "new_election2" added' in output_text)
                self.assertTrue("There are no candidates." in output_text)
                self.assertIn(
                    'input class="form-control" id="admin_grp" '
                    'name="admin_grp" type="text" '
                    'value="sysadmin-main, testers">',
                    output_text,
                )
                self.assertIn(
                    'input class="form-control" id="lgl_voters" '
                    'name="lgl_voters" type="text" '
                    'value="packager, testers">',
                    output_text,
                )
                self.assertIn(
                    'input class="form-control" id="max_votes" '
                    'name="max_votes" type="text" '
                    'value="">',
                    output_text,
                )

    def test_admin_edit_election(self):
        """ Test the admin_edit_election function. """
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/")
                self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Election Details" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )

                data = {
                    "alias": "test_election",
                    "shortdesc": "test election shortdesc",
                    "description": "test election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY - timedelta(days=10),
                    "end_date": TODAY - timedelta(days=8),
                    "seats_elected": "2",
                    "candidates_are_fasusers": False,
                    "embargoed": False,
                }

                output = self.app.post("/admin/test_election/", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Election Details" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )

                csrf_token = self.get_csrf()

                data = {
                    "alias": "test_election",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY - timedelta(days=10),
                    "end_date": TODAY - timedelta(days=8),
                    "seats_elected": "2",
                    "candidates_are_fasusers": False,
                    "embargoed": False,
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/admin/test_election/", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Election Details" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" required type="text" ',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="shortdesc" '
                        'name="shortdesc" type="text" ',
                        output_text,
                    )
                self.assertIn(
                    '<div class="form-control-feedback">This field is required.</div>',
                    output_text,
                )

                # Check election before edit
                output = self.app.get("/admin/test_election/")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">3</span>'
                    in output_text
                )
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text" '
                        'value="1">',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text" '
                        'value="1">',
                        output_text,
                    )

                data = {
                    "alias": "test_election",
                    "shortdesc": "test election shortdesc",
                    "description": "test election description",
                    "voting_type": "simple",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY - timedelta(days=10),
                    "end_date": TODAY - timedelta(days=8),
                    "seats_elected": "2",
                    "candidates_are_fasusers": False,
                    "embargoed": False,
                    "max_votes": "wrong",
                    "csrf_token": csrf_token,
                }

                with mock_sends(EditElectionV1):
                    output = self.app.post(
                        "/admin/test_election/", data=data, follow_redirects=True
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Election "test_election" saved' in output_text)
                # We edited the seats_elected from 1 to 2
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text" '
                        'value="2">',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text" '
                        'value="2">',
                        output_text,
                    )
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">3</span>'
                    in output_text
                )

    def test_admin_edit_election_admin_groups(self):
        """Test the admin_edit_election function when editing admin groups."""
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/edit")
                self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election2/")
                self.assertEqual(output.status_code, 200)
                csrf_token = self.get_csrf(output=output)

                # Edit Admin Group

                # Check election before edit
                output = self.app.get("/admin/test_election2/")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text" '
                        'value="1">',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text" '
                        'value="1">',
                        output_text,
                    )
                self.assertTrue('Candidates <span class="label' in output_text)

                # Add a new admin group: sysadmin-main
                data = {
                    "alias": "test_election2",
                    "shortdesc": "test election 2 shortdesc",
                    "description": "test election 2 description",
                    "voting_type": "range",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY - timedelta(days=7),
                    "end_date": TODAY - timedelta(days=5),
                    "seats_elected": "2",
                    "candidates_are_fasusers": False,
                    "embargoed": False,
                    "admin_grp": "testers, sysadmin-main",
                    "csrf_token": csrf_token,
                }

                with mock_sends(EditElectionV1):
                    output = self.app.post(
                        "/admin/test_election2/", data=data, follow_redirects=True
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Election "test_election2" saved' in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text" '
                        'value="2">',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text" '
                        'value="2">',
                        output_text,
                    )
                # We edited the admin groups
                self.assertIn(
                    'input class="form-control" id="admin_grp" '
                    'name="admin_grp" type="text" '
                    'value="sysadmin-main, testers">',
                    output_text,
                )

                # Remove an existing group: testers
                data = {
                    "alias": "test_election2",
                    "shortdesc": "test election 2 shortdesc",
                    "description": "test election 2 description",
                    "voting_type": "range",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY - timedelta(days=7),
                    "end_date": TODAY - timedelta(days=5),
                    "seats_elected": "2",
                    "candidates_are_fasusers": False,
                    "embargoed": False,
                    "admin_grp": "sysadmin-main",
                    "csrf_token": csrf_token,
                }

                with mock_sends(EditElectionV1):
                    output = self.app.post(
                        "/admin/test_election2/", data=data, follow_redirects=True
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Election "test_election2" saved' in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text" '
                        'value="2">',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text" '
                        'value="2">',
                        output_text,
                    )
                # We edited the admin groups
                self.assertIn(
                    'input class="form-control" id="admin_grp" '
                    'name="admin_grp" type="text" '
                    'value="sysadmin-main">',
                    output_text,
                )

    def test_admin_edit_election_legal_voters(self):
        """Test the admin_edit_election function when editing legal voters."""
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/edit")
                self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election3/")
                self.assertEqual(output.status_code, 200)
                csrf_token = self.get_csrf(output=output)
                # Edit LegalVoter Group

                # Check election before edit
                output = self.app.get("/admin/test_election3/")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text"',
                        output_text,
                    )
                self.assertTrue('Candidates <span class="label' in output_text)
                self.assertTrue(
                    '<input class="form-control" id="admin_grp" name="admin_grp" type="text" value="">'
                    in output_text
                )
                self.assertIn(
                    'input class="form-control" id="lgl_voters" '
                    'name="lgl_voters" type="text" value="voters">',
                    output_text,
                )

                # Add a new admin group: sysadmin-main
                data = {
                    "alias": "test_election3",
                    "shortdesc": "test election 3 shortdesc",
                    "description": "test election 3 description",
                    "voting_type": "range",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY - timedelta(days=2),
                    "end_date": TODAY + timedelta(days=3),
                    "seats_elected": "1",
                    "candidates_are_fasusers": False,
                    "embargoed": False,
                    "lgl_voters": "voters, sysadmin-main",
                    "csrf_token": csrf_token,
                }

                with mock_sends(EditElectionV1):
                    output = self.app.post(
                        "/admin/test_election3/", data=data, follow_redirects=True
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Election "test_election3" saved' in output_text)
                # We edited the legal_voters
                self.assertIn(
                    'input class="form-control" id="lgl_voters" '
                    'name="lgl_voters" type="text" '
                    'value="sysadmin-main, voters">',
                    output_text,
                )

                # Remove an existing group: voters
                data = {
                    "alias": "test_election3",
                    "shortdesc": "test election 3 shortdesc",
                    "description": "test election 3 description",
                    "voting_type": "range",
                    "url": "https://fedoraproject.org",
                    "start_date": TODAY - timedelta(days=2),
                    "end_date": TODAY + timedelta(days=3),
                    "seats_elected": "1",
                    "candidates_are_fasusers": False,
                    "embargoed": False,
                    "lgl_voters": "sysadmin-main",
                    "csrf_token": csrf_token,
                }

                with mock_sends(EditElectionV1):
                    output = self.app.post(
                        "/admin/test_election3/", data=data, follow_redirects=True
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Election "test_election3" saved' in output_text)
                # We edited the legal_voters
                self.assertIn(
                    'input class="form-control" id="lgl_voters" '
                    'name="lgl_voters" type="text" '
                    'value="sysadmin-main">',
                    output_text,
                )

    def test_admin_add_candidate(self):
        """ Test the admin_add_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/candidates/new")
                self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/candidates/new")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                self.assertTrue("Add candidate" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'type="text"',
                        output_text,
                    )

                data = {
                    "name": "pingou",
                    "url": "",
                }

                output = self.app.post("/admin/test_election/candidates/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Add candidate" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'type="text"',
                        output_text,
                    )

                csrf_token = self.get_csrf(output=output)

                data = {
                    "name": "",
                    "url": "",
                    "csrf_token": csrf_token,
                }

                output = self.app.post("/admin/test_election/candidates/new", data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Add candidate" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'type="text"',
                        output_text,
                    )
                self.assertTrue(
                    '<div class="form-control-feedback">This field is required.</div>'
                    in output_text
                )

                data = {
                    "name": "pingou",
                    "url": "",
                    "csrf_token": csrf_token,
                }

                with mock_sends(NewCandidateV1):
                    output = self.app.post(
                        "/admin/test_election/candidates/new",
                        data=data,
                        follow_redirects=True,
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Candidate "pingou" saved' in output_text)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">4</span>'
                    in output_text
                )

    def test_admin_add_multi_candidate(self):
        """ Test the admin_add_multi_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/candidates/new/multi")
                self.assertEqual(output.status_code, 404)

        self.setup_db()

        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test_election/candidates/new/multi")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                self.assertTrue("Add candidates" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="candidate" '
                        'name="candidate" required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="candidate" '
                        'name="candidate" type="text"',
                        output_text,
                    )

                data = {
                    "candidate": "pingou",
                }

                output = self.app.post(
                    "/admin/test_election/candidates/new/multi", data=data
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Add candidates" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="candidate" '
                        'name="candidate" required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="candidate" '
                        'name="candidate" type="text"',
                        output_text,
                    )

                csrf_token = self.get_csrf(output=output)

                data = {
                    "candidate": "",
                    "csrf_token": csrf_token,
                }

                output = self.app.post(
                    "/admin/test_election/candidates/new/multi", data=data
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Add candidates" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="candidate" '
                        'name="candidate" required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="candidate" '
                        'name="candidate" type="text"',
                        output_text,
                    )
                self.assertTrue(
                    '<div class="form-control-feedback">This field is required.</div>'
                    in output_text
                )

                data = {
                    "candidate": "pingou|patrick!https://fedoraproject.org|"
                    "shaiton!https://fedoraproject.org!test|sochotni",
                    "csrf_token": csrf_token,
                }

                with mock_sends(NewCandidateV1, NewCandidateV1, NewCandidateV1):
                    output = self.app.post(
                        "/admin/test_election/candidates/new/multi",
                        data=data,
                        follow_redirects=True,
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Added 3 candidates" in output_text)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">6</span>'
                    in output_text
                )

    def test_admin_edit_candidate(self):
        """ Test the admin_edit_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        self.setup_db()

        # Election does not exist
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test/candidates/1/edit")
                self.assertEqual(output.status_code, 404)

                # Candidate does not exist
                output = self.app.get("/admin/test_election/candidates/100/edit")
                self.assertEqual(output.status_code, 404)

                # Candidate not in election
                output = self.app.get("/admin/test_election/candidates/5/edit")
                self.assertEqual(output.status_code, 404)

                output = self.app.get("/admin/test_election/candidates/1/edit")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                self.assertTrue("Edit candidate" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'type="text"',
                        output_text,
                    )

                data = {
                    "name": "Toshio Kuratomi",
                    "url": "https://fedoraproject.org/wiki/User:Toshio",
                }

                self.assertTrue("Edit candidate" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'type="text"',
                        output_text,
                    )

                csrf_token = self.get_csrf(output=output)

                data = {
                    "name": "",
                    "csrf_token": csrf_token,
                }

                output = self.app.post(
                    "/admin/test_election/candidates/1/edit", data=data
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("Edit candidate" in output_text)
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'required type="text"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="name" name="name" '
                        'type="text"',
                        output_text,
                    )
                self.assertTrue(
                    '<div class="form-control-feedback">This field is required.</div>'
                    in output_text
                )

                # Check election before edit
                output = self.app.get("/admin/test_election/")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">3</span>'
                    in output_text
                )
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text" value="1"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text" value="1"',
                        output_text,
                    )
                self.assertTrue('<div class="list-group-item">Toshio' in output_text)

                data = {
                    "name": "Toshio Kuratomi",
                    "url": "https://fedoraproject.org/wiki/User:Toshio",
                    "csrf_token": csrf_token,
                }

                with mock_sends(EditCandidateV1):
                    output = self.app.post(
                        "/admin/test_election/candidates/1/edit",
                        data=data,
                        follow_redirects=True,
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Candidate "Toshio Kuratomi" saved' in output_text)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">3</span>'
                    in output_text
                )
                self.assertTrue('<div class="list-group-item">Toshio' in output_text)

    def test_admin_delete_candidate(self):
        """ Test the admin_delete_candidate function. """
        user = FakeUser(
            fedora_elections.APP.config["FEDORA_ELECTIONS_ADMIN_GROUP"],
            username="toshio",
        )

        self.setup_db()

        # Election does not exist
        with user_set(fedora_elections.APP, user, oidc_id_token="foobar"):
            with patch(
                "fedora_elections.OIDC.user_getfield",
                MagicMock(return_value=["elections"]),
            ):
                output = self.app.get("/admin/test/candidates/1/delete")
                self.assertEqual(output.status_code, 404)

                # Candidate does not exist
                output = self.app.get("/admin/test_election/candidates/100/delete")
                self.assertEqual(output.status_code, 404)

                # Candidate not in election
                output = self.app.get("/admin/test_election/candidates/5/delete")
                self.assertEqual(output.status_code, 404)

                output = self.app.get("/admin/test_election/candidates/1/delete")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)

                self.assertTrue("<h2>Delete candidate</h2>" in output_text)
                self.assertTrue(
                    'p>Are you sure you want to delete candidate "Toshio"?</p'
                    in output_text
                )

                output = self.app.post("/admin/test_election/candidates/1/delete")
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>Delete candidate</h2>" in output_text)
                self.assertTrue(
                    'p>Are you sure you want to delete candidate "Toshio"?</p'
                    in output_text
                )

                csrf_token = self.get_csrf(output=output)

                # Try to delete while there are votes link to this candidates
                data = {
                    "csrf_token": csrf_token,
                }

                output = self.app.post(
                    "/admin/test_election/candidates/1/delete",
                    data=data,
                    follow_redirects=True,
                )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue("<h2>test election shortdesc</h2>" in output_text)
                self.assertTrue(
                    "Could not delete this candidate. Is it "
                    "already part of an election?" in output_text
                )

                # Check election before edit
                output = self.app.get("/admin/test_election4/")
                output_text = output.get_data(as_text=True)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">2</span>'
                    in output_text
                )
                if self.get_wtforms_version() >= (2, 2):
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" required type="text" value="1"',
                        output_text,
                    )
                else:
                    self.assertIn(
                        'input class="form-control" id="seats_elected" '
                        'name="seats_elected" type="text" value="1"',
                        output_text,
                    )
                self.assertTrue('<div class="list-group-item">Toshio' in output_text)
                self.assertTrue('value="test election 4 shortdesc">' in output_text)

                # Delete one candidate
                data = {
                    "csrf_token": csrf_token,
                }

                with mock_sends(DeleteCandidateV1):
                    output = self.app.post(
                        "/admin/test_election4/candidates/10/delete",
                        data=data,
                        follow_redirects=True,
                    )
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertTrue('Candidate "Toshio" deleted' in output_text)
                self.assertTrue('value="test election 4 shortdesc">' in output_text)
                self.assertTrue(
                    'Candidates <span class="label label-pill label-default">1</span>'
                    in output_text
                )
                self.assertFalse('<div class="list-group-item">Toshio' in output_text)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskAdmintests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
