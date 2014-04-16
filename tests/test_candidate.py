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

 fedora_elections.model.Candidate test script
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
from test_election import Electiontests


# pylint: disable=R0904
class Candidatetests(Modeltests):
    """ Candidate tests. """

    session = None

    def test_init_candidate(self):
        """ Test the Candidate init function. """
        elections = Electiontests('test_init_election')
        elections.session = self.session
        elections.test_init_election()

        ## Election #1

        obj = models.Candidate(  # id:1
            election_id=1,
            name='Toshio',
            url='https://fedoraproject.org/wiki/User:Toshio',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:2
            election_id=1,
            name='Kevin',
            url='https://fedoraproject.org/wiki/User:Kevin',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:3
            election_id=1,
            name='Ralph',
            url='https://fedoraproject.org/wiki/User:Ralph',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        ## Election #5

        obj = models.Candidate(  # id:4
            election_id=5,
            name='Toshio',
            url='https://fedoraproject.org/wiki/User:Toshio',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:5
            election_id=5,
            name='Kevin',
            url='https://fedoraproject.org/wiki/User:Kevin',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:6
            election_id=5,
            name='Ralph',
            url='https://fedoraproject.org/wiki/User:Ralph',
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_to_json(self):
        """ Test the Candidate.to_json function. """
        self.test_init_candidate()
        obj = models.Candidate.by_id(self.session, 3)
        self.assertEqual(
            obj.to_json(),
            {
                'name': 'Ralph',
                'url': 'https://fedoraproject.org/wiki/User:Ralph',
            }
        )

        obj = models.Candidate.get(self.session, 2)
        self.assertEqual(
            obj.to_json(),
            {
                'name': 'Kevin',
                'url': 'https://fedoraproject.org/wiki/User:Kevin',
            }
        )

    def test_vote_count(self):
        """ Test the Candidate.vote_count function. """
        self.test_init_candidate()

        obj = models.Candidate.by_id(self.session, 3)
        self.assertEqual(obj.vote_count, 0)

        obj = models.Candidate.get(self.session, 2)
        self.assertEqual(obj.vote_count, 0)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Candidatetests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
