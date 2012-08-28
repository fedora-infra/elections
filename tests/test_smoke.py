# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Red Hat, Inc.
#
# Author(s): Toshio Kuratomi <toshio@fedoraproject.org>

from copy import copy
import datetime
from functools import partial

from mock import Mock
from nose import tools, with_setup

from base import BaseRequestTests, anon_urls, authed_view_urls, \
        admin_view_urls, admin_modify_urls, url_subs

from fedora_elections import db, models
from fedora_elections import fas

class TestSmoke(BaseRequestTests):
    '''Basic test that we don't get 500s'''

    def setUp(self):
        super(TestSmoke, self).setUp()
        fas.login = Mock(return_value=True)
        # Add an election
        election = models.Election(summary='Test Election 1',
                alias='test1', description='lorem ipsum of course',
                url='http://fedorahosted.org/elections',
                start_date=datetime.datetime.utcnow(),
                end_date=datetime.datetime.utcnow()+datetime.timedelta(hours=1))
        db.session.add(election)
        # Add candidate to election
        candidate = models.Candidate(election=election, name='Mr Testy', url='http://fedoraproject.org')
        db.session.add(candidate)
        db.session.commit()

        self.url_subs = copy(url_subs)
        self.url_subs['election_alias'] = 'test1'
        self.url_subs['candidate_id'] = candidate.id

    def tearDown(self):
        super(TestSmoke, self).tearDown()

    def setup_auth(self, username, password):
        self.setUp()
        self.app.post('/login', data=dict( username=username,
            password=password), follow_redirects=True)

    def teardown_auth(self):
        self.tearDown()
        return self.app.get('/logout', follow_redirects=True)

    def check_status_code(self, url, status_codes=[200]):
        resp = self.app.get(url % self.url_subs, follow_redirects=True)
        tools.assert_in(resp.status_code, status_codes)

    @with_setup(partial(setup_auth, 'user', '123'), teardown_auth)
    def check_user_status_code(self, *args, **kwargs):
        self.check_status_code(*args, **kwargs)

    @with_setup(partial(setup_auth, 'admin', '123'), teardown_auth)
    def check_admin_status_code(self, *args, **kwargs):
        self.check_status_code(*args, **kwargs)

    def test_all_url_subs(self):
        '''Testing that the testsuite is going to substitute all variables in the url.'''
        for i in self.url_subs.values():
            if i is None:
                raise Exception('Smoke test must be updated for new url variable present in base.py')

    def test_anon_view(self):
        for url in anon_urls:
            yield self.check_status_code, url, [200]

    def test_authed_view(self):
        for url in (u for u in authed_view_urls):
            yield self.check_user_status_code, url, [200]

    def test_admin_view(self):
        for url in (u for u in admin_view_urls):
            yield self.check_admin_status_code, url, [200]

    def test_admin_modify(self):
        for url in (u for u in admin_modify_urls):
            yield self.check_admin_status_code, url, [200]
