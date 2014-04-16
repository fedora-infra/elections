#!/usr/bin/python
#-*- coding: utf-8 -*-

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

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from fedora_elections import models
from tests import Modeltests, TODAY


# pylint: disable=R0904
class Electiontests(Modeltests):
    """ Election tests. """

    session = None

    def test_init_election(self):
        """ Test the Election init function. """
        # Election finished - result open
        obj = models.Election(  # id:1
            shortdesc='test election shortdesc',
            alias='test_election',
            description='test election description',
            url='https://fedoraproject.org',
            start_date=TODAY - timedelta(days=10),
            end_date=TODAY - timedelta(days=8),
            seats_elected=1,
            embargoed=0,
            voting_type='range',
            candidates_are_fasusers=0,
            fas_user='ralph',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Election finished - result embargoed
        obj = models.Election(  # id:2
            shortdesc='test election 2 shortdesc',
            alias='test_election2',
            description='test election 2 description',
            url='https://fedoraproject.org',
            start_date=TODAY - timedelta(days=7),
            end_date=TODAY - timedelta(days=5),
            seats_elected=1,
            embargoed=1,
            voting_type='range',
            candidates_are_fasusers=0,
            fas_user='kevin',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Election open
        obj = models.Election(  # id:3
            shortdesc='test election 3 shortdesc',
            alias='test_election3',
            description='test election 3 description',
            url='https://fedoraproject.org',
            start_date=TODAY - timedelta(days=2),
            end_date=TODAY + timedelta(days=2),
            seats_elected=1,
            embargoed=1,
            voting_type='range',
            candidates_are_fasusers=0,
            fas_user='pingou',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Election created but not open
        obj = models.Election(  # id:4
            shortdesc='test election 4 shortdesc',
            alias='test_election4',
            description='test election 4 description',
            url='https://fedoraproject.org',
            start_date=TODAY + timedelta(days=3),
            end_date=TODAY + timedelta(days=6),
            seats_elected=1,
            embargoed=1,
            voting_type='range',
            candidates_are_fasusers=0,
            fas_user='skvidal',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_get_election(self):
        """ Test the Election.get function. """
        self.test_init_election()
        obj = models.Election.get(self.session, 'test_election')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.id, 1)

    def test_status_election(self):
        """ Test the Election.status function. """
        self.test_init_election()
        obj = models.Election.get(self.session, 'test_election')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.status, 'Ended')

        obj = models.Election.get(self.session, 'test_election2')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.status, 'Embargoed')

        obj = models.Election.get(self.session, 'test_election3')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.status, 'In progress')

        obj = models.Election.get(self.session, 'test_election4')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.status, 'Pending')

    def test_locked_election(self):
        """ Test the Election.locked function. """
        self.test_init_election()
        obj = models.Election.get(self.session, 'test_election')
        self.assertNotEqual(obj, None)
        self.assertTrue(obj.locked)

        obj = models.Election.get(self.session, 'test_election2')
        self.assertNotEqual(obj, None)
        self.assertTrue(obj.locked)

        obj = models.Election.get(self.session, 'test_election3')
        self.assertNotEqual(obj, None)
        self.assertTrue(obj.locked)

        obj = models.Election.get(self.session, 'test_election4')
        self.assertNotEqual(obj, None)
        self.assertFalse(obj.locked)

    def test_search_election(self):
        """ Test the Election.search function. """
        self.test_init_election()
        obj = models.Election.search(self.session, alias='test_election')
        self.assertNotEqual(obj, None)
        self.assertNotEqual(obj, [])
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].shortdesc, 'test election shortdesc')

        obj = models.Election.search(
            self.session, shortdesc='test election 2 shortdesc')
        self.assertNotEqual(obj, None)
        self.assertNotEqual(obj, [])
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].description, 'test election 2 description')

        obj = models.Election.search(
            self.session, fas_user='skvidal')
        self.assertNotEqual(obj, None)
        self.assertNotEqual(obj, [])
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].description, 'test election 4 description')

        obj = models.Election.search(self.session)
        self.assertNotEqual(obj, None)
        self.assertNotEqual(obj, [])
        self.assertEqual(len(obj), 4)
        self.assertEqual(obj[0].description, 'test election 4 description')
        self.assertEqual(obj[1].description, 'test election 3 description')
        self.assertEqual(obj[2].description, 'test election 2 description')
        self.assertEqual(obj[3].description, 'test election description')

    def test_get_older_election(self):
        """ Test the Election.get_older_election function. """
        self.test_init_election()
        obj = models.Election.get_older_election(self.session, limit=TODAY)
        self.assertNotEqual(obj, None)
        self.assertNotEqual(obj, [])
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0].shortdesc, 'test election 2 shortdesc')
        self.assertEqual(obj[1].shortdesc, 'test election shortdesc')

    def test_get_open_election(self):
        """ Test the Election.get_open_election function. """
        self.test_init_election()
        obj = models.Election.get_open_election(self.session, limit=TODAY)
        self.assertNotEqual(obj, None)
        self.assertNotEqual(obj, [])
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].shortdesc, 'test election 3 shortdesc')

    def test_get_next_election(self):
        """ Test the Election.get_next_election function. """
        self.test_init_election()
        obj = models.Election.get_next_election(self.session, limit=TODAY)
        self.assertNotEqual(obj, None)
        self.assertNotEqual(obj, [])
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].shortdesc, 'test election 4 shortdesc')

    def test_to_json(self):
        """ Test the Election.to_json function. """
        self.test_init_election()
        obj = models.Election.get(self.session, 'test_election')
        self.assertEqual(
            obj.to_json(),
            {
                'description': 'test election description',
                'end_date': (
                    TODAY - timedelta(days=8)).strftime('%Y-%m-%d %H:%M'),
                'url': 'https://fedoraproject.org',
                'embargoed': 0,
                'alias': 'test_election',
                'shortdesc': 'test election shortdesc',
                'voting_type': 'range',
                'start_date': (
                    TODAY - timedelta(days=10)).strftime('%Y-%m-%d %H:%M'),
            }
        )


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Electiontests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
