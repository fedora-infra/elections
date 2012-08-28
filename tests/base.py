# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Red Hat, Inc.
#
# Author(s):        Toshio Kuratomi <toshio@fedoraproject.org>

import fedora_elections

# Note: This is used in unittests that use nose's generator tests so we can't
# subclass unittest.TestCase
class BaseRequestTests(object):
    '''Setup application for further testing of requests'''

    def setUp(self):
        fedora_elections.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + '../tests/testing.db'
        fedora_elections.app.config['TESTING'] = True
        self.app = fedora_elections.app.test_client()
        fedora_elections.db.create_all()

    def tearDown(self):
        fedora_elections.db.session.remove()
        fedora_elections.db.drop_all()

url_subs = {'election_alias': None, 'candidate_id': None}
anon_urls = ('/', '/archive', '/login', '/logout', '/vote/%(election_alias)s')
authed_view_urls = ('/logout', '/vote/%(election_alias)s')
admin_view_urls = ('/admin', '/admin/new', '/admin/%(election_alias)s')
admin_modify_urls = ('/admin/new', '/admin/%(election_alias)s/edit',
    '/admin/%(election_alias)s/candidates/new',
    '/admin/%(election_alias)s/candidates/%(candidate_id)d/edit',
    '/admin/%(election_alias)s/candidates/%(candidate_id)d/delete')
