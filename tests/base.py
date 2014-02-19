# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2014 Red Hat, Inc.
#
# Author(s):        Toshio Kuratomi <toshio@fedoraproject.org>

import os

import fedora_elections
from fedora_elections.models import create_tables

# Note: This is used in unittests that use nose's generator tests so we can't
# subclass unittest.TestCase
class BaseRequestTests(object):
    '''Setup application for further testing of requests'''

    def setUp(self):
        cur_folder = os.path.dirname(os.path.realpath(__file__))
        db_file = os.path.join(cur_folder, 'testing.sqlite')
        print '* creating %s' % db_file
        fedora_elections.APP.config['DB_URL'] = 'sqlite:///%s' % db_file

        self.session = create_tables(fedora_elections.APP.config['DB_URL'])

        fedora_elections.APP.config['TESTING'] = True
        fedora_elections.APP.SESSION = self.session
        self.app = fedora_elections.APP.test_client()

    def tearDown(self):
        cur_folder = os.path.dirname(os.path.realpath(__file__))
        db_file = os.path.join(cur_folder, 'testing.sqlite')
        print '* cleaning %s' % db_file
        os.unlink(db_file)


url_subs = {'election_alias': None, 'candidate_id': None}

anon_urls = (
    '/',
    '/archive',
    '/login',
    '/logout',
    '/vote/%(election_alias)s')

authed_view_urls = (
    '/logout',
    '/vote/%(election_alias)s')

admin_view_urls = (
    '/admin',
    '/admin/new',
    '/admin/%(election_alias)s')

admin_modify_urls = (
    '/admin/new',
    '/admin/%(election_alias)s/edit',
    '/admin/%(election_alias)s/candidates/new',
    '/admin/%(election_alias)s/candidates/%(candidate_id)d/edit',
    '/admin/%(election_alias)s/candidates/%(candidate_id)d/delete')

