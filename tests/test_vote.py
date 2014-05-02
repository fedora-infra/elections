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

 fedora_elections.model.Vote test script
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
from test_candidate import Candidatetests


# pylint: disable=R0904
class Votetests(Modeltests):
    """ Vote tests. """

    session = None

    def test_init_vote(self):
        """ Test the Vote init function. """
        candidates = Candidatetests('test_init_candidate')
        candidates.session = self.session
        candidates.test_init_candidate()

        obj = models.Vote(  # id:1
            election_id=1,
            voter='toshio',
            candidate_id=1,
            value='3',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:2
            election_id=1,
            voter='toshio',
            candidate_id=2,
            value='3',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:3
            election_id=1,
            voter='toshio',
            candidate_id=3,
            value='3',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:4
            election_id=1,
            voter='ralph',
            candidate_id=2,
            value=2,
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:5
            election_id=1,
            voter='ralph',
            candidate_id=3,
            value=1,
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Election 3

        obj = models.Vote(  # id:1
            election_id=3,
            voter='toshio',
            candidate_id=1,
            value='3',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:2
            election_id=3,
            voter='toshio',
            candidate_id=2,
            value='3',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:4
            election_id=3,
            voter='toshio',
            candidate_id=3,
            value='3',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Election 5

        obj = models.Vote(  # id:1
            election_id=5,
            voter='toshio',
            candidate_id=7,
            value='1',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:2
            election_id=5,
            voter='toshio',
            candidate_id=8,
            value='1',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Vote(  # id:4
            election_id=5,
            voter='kevin',
            candidate_id=9,
            value='1',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_vote_count_with_votes(self):
        """ Test the Candidate.vote_count function with votes in. """
        self.test_init_vote()

        obj = models.Candidate.get(self.session, 2)
        self.assertEqual(obj.vote_count, 8)

        obj = models.Candidate.get(self.session, 1)
        self.assertEqual(obj.vote_count, 6)

        obj = models.Candidate.by_id(self.session, 3)
        self.assertEqual(obj.vote_count, 7)

    def test_of_user_on_election(self):
        """ Test the Vote.of_user_on_election function. """
        self.test_init_vote()

        obj = models.Vote.of_user_on_election(
            self.session, 'toshio', 1, count=True)
        self.assertEqual(obj, 3)

        obj = models.Vote.of_user_on_election(
            self.session, 'toshio', 1, count=False)
        self.assertEqual(len(obj), 3)
        self.assertEqual(obj[0].voter, 'toshio')
        self.assertEqual(obj[0].candidate.name, 'Toshio')
        self.assertEqual(obj[1].voter, 'toshio')
        self.assertEqual(obj[1].candidate.name, 'Kevin')
        self.assertEqual(obj[2].voter, 'toshio')
        self.assertEqual(obj[2].candidate.name, 'Ralph')

    def test_get_election_stats(self):
        """ Test the get_election_stats function. """
        self.test_init_vote()

        obj = models.Vote.get_election_stats(self.session, 1)
        self.assertEqual(obj['n_voters'], 2)
        self.assertEqual(obj['n_votes'], 5)
        self.assertEqual(
            obj['candidate_voters'],
            {'Toshio': 1, 'Ralph': 2, 'Kevin': 2}
        )
        self.assertEqual(obj['n_candidates'], 3)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Votetests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
