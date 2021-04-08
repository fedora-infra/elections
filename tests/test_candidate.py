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

 fedora_elections.model.Candidate test script
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from fedora_elections import models  # noqa:E402

from tests import Modeltests  # noqa: E402
from tests.test_election import Electiontests  # noqa:E402


# pylint: disable=R0904
class Candidatetests(Modeltests):
    """ Candidate tests. """

    session = None

    def test_init_candidate(self):
        """ Test the Candidate init function. """
        elections = Electiontests("test_init_election")
        elections.session = self.session
        elections.test_init_election()

        #
        # Election #1
        #

        obj = models.Candidate(  # id:1
            election_id=1,
            name="Toshio",
            url="https://fedoraproject.org/wiki/User:Toshio",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:2
            election_id=1,
            name="Kevin",
            url="https://fedoraproject.org/wiki/User:Kevin",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:3
            election_id=1,
            name="Ralph",
            url="https://fedoraproject.org/wiki/User:Ralph",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        #
        # Election #3
        #

        obj = models.Candidate(  # id:4
            election_id=3,
            name="Toshio",
            url="https://fedoraproject.org/wiki/User:Toshio",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:5
            election_id=3,
            name="Kevin",
            url="https://fedoraproject.org/wiki/User:Kevin",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:6
            election_id=3,
            name="Ralph",
            url="https://fedoraproject.org/wiki/User:Ralph",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        #
        # Election #5
        #

        obj = models.Candidate(  # id:7
            election_id=5,
            name="Toshio",
            url="https://fedoraproject.org/wiki/User:Toshio",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:8
            election_id=5,
            name="Kevin",
            url="https://fedoraproject.org/wiki/User:Kevin",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:9
            election_id=5,
            name="Ralph",
            url="https://fedoraproject.org/wiki/User:Ralph",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        #
        # Election #4
        #

        obj = models.Candidate(  # id:10
            election_id=4,
            name="Toshio",
            url="https://fedoraproject.org/wiki/User:Toshio",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:11
            election_id=4,
            name="Kevin",
            url="https://fedoraproject.org/wiki/User:Kevin",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        #
        # Election #6
        #

        obj = models.Candidate(  # id:12
            election_id=6,
            name="Toshio",
            url="https://fedoraproject.org/wiki/User:Toshio",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:13
            election_id=6,
            name="Kevin",
            url="https://fedoraproject.org/wiki/User:Kevin",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        #
        # Election #7
        #

        obj = models.Candidate(  # id:14
            election_id=7,
            name="Toshio",
            url="https://fedoraproject.org/wiki/User:Toshio",
        )
        self.session.add(obj)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = models.Candidate(  # id:15
            election_id=7,
            name="Kevin",
            url="https://fedoraproject.org/wiki/User:Kevin",
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
                "name": "Ralph",
                "url": "https://fedoraproject.org/wiki/User:Ralph",
                "fas_name": None,
            },
        )

        obj = models.Candidate.get(self.session, 2)
        self.assertEqual(
            obj.to_json(),
            {
                "name": "Kevin",
                "url": "https://fedoraproject.org/wiki/User:Kevin",
                "fas_name": None,
            },
        )

    def test_vote_count(self):
        """ Test the Candidate.vote_count function. """
        self.test_init_candidate()

        obj = models.Candidate.by_id(self.session, 3)
        self.assertEqual(obj.vote_count, 0)

        obj = models.Candidate.get(self.session, 2)
        self.assertEqual(obj.vote_count, 0)


if __name__ == "__main__":
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Candidatetests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
