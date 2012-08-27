# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Red Hat, Inc.
#
# Author(s):        Toshio Kuratomi <toshio@fedoraproject.org>

from functools import partial

from nose import tools, with_setup

from base import BaseRequestTests, anon_urls, authed_urls, admin_urls

class TestSmoke(BaseRequestTests):
    '''Basic test that we don't get 500s'''

    def setUp(self):
        super(TestSmoke, self).setUp()

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
        resp = self.app.get(url, follow_redirects=True)
        tools.assert_in(resp.status_code, status_codes)

    @with_setup(partial(setup_auth, 'user', '123'), teardown_auth)
    def check_user_status_code(self, *args, **kwargs):
        self.check_status_code(*args, **kwargs)

    @with_setup(partial(setup_auth, 'admin', '123'), teardown_auth)
    def check_admin_status_code(self, *args, **kwargs):
        self.check_status_code(*args, **kwargs)

    def test_anon(self):
        for url in anon_urls:
            yield self.check_status_code, url, [200]

    def test_authed(self):
        for url in (u for u in authed_urls):
            yield self.check_user_status_code, url, [200]

    def test_admin(self):
        self.setup_auth('admin', '123')
        for url in (u for u in admin_urls):
            yield self.check_admin_status_code, url, [200]
