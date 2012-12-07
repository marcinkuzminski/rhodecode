from __future__ import with_statement
import os
import csv
import datetime
from rhodecode.tests import *
from rhodecode.model.db import UserLog
from rhodecode.model.meta import Session
from rhodecode.lib.utils2 import safe_unicode

dn = os.path.dirname
FIXTURES = os.path.join(dn(dn(os.path.abspath(__file__))), 'fixtures')


class TestAdminController(TestController):

    @classmethod
    def setup_class(cls):
        UserLog.query().delete()
        Session().commit()

        def strptime(val):
            fmt = '%Y-%m-%d %H:%M:%S'
            if '.' not in val:
                return datetime.datetime.strptime(val, fmt)

            nofrag, frag = val.split(".")
            date = datetime.datetime.strptime(nofrag, fmt)

            frag = frag[:6]  # truncate to microseconds
            frag += (6 - len(frag)) * '0'  # add 0s
            return date.replace(microsecond=int(frag))

        with open(os.path.join(FIXTURES, 'journal_dump.csv')) as f:
            for row in csv.DictReader(f):
                ul = UserLog()
                for k, v in row.iteritems():
                    v = safe_unicode(v)
                    if k == 'action_date':
                        v = strptime(v)
                    if k in ['user_id', 'repository_id']:
                        # nullable due to FK problems
                        v = None
                    setattr(ul, k, v)
                Session().add(ul)
            Session().commit()

    @classmethod
    def teardown_class(cls):
        UserLog.query().delete()
        Session().commit()

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index'))
        response.mustcontain('Admin journal')

    def test_filter_all_entries(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',))
        response.mustcontain('2034 entries')

    def test_filter_journal_filter_exact_match_on_repository(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='repository:rhodecode'))
        response.mustcontain('3 entries')

    def test_filter_journal_filter_exact_match_on_repository_CamelCase(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='repository:RhodeCode'))
        response.mustcontain('3 entries')

    def test_filter_journal_filter_wildcard_on_repository(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='repository:*test*'))
        response.mustcontain('862 entries')

    def test_filter_journal_filter_prefix_on_repository(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='repository:test*'))
        response.mustcontain('257 entries')

    def test_filter_journal_filter_prefix_on_repository_CamelCase(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='repository:Test*'))
        response.mustcontain('257 entries')

    def test_filter_journal_filter_prefix_on_repository_and_user(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='repository:test* AND username:demo'))
        response.mustcontain('130 entries')

    def test_filter_journal_filter_prefix_on_repository_or_other_repo(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='repository:test* OR repository:rhodecode'))
        response.mustcontain('260 entries')  # 257 + 3

    def test_filter_journal_filter_exact_match_on_username(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='username:demo'))
        response.mustcontain('1087 entries')

    def test_filter_journal_filter_exact_match_on_username_camelCase(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='username:DemO'))
        response.mustcontain('1087 entries')

    def test_filter_journal_filter_wildcard_on_username(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='username:*test*'))
        response.mustcontain('100 entries')

    def test_filter_journal_filter_prefix_on_username(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='username:demo*'))
        response.mustcontain('1101 entries')

    def test_filter_journal_filter_prefix_on_user_or_other_user(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='username:demo OR username:volcan'))
        response.mustcontain('1095 entries')  # 1087 + 8

    def test_filter_journal_filter_wildcard_on_action(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='action:*pull_request*'))
        response.mustcontain('187 entries')

    def test_filter_journal_filter_on_date(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='date:20121010'))
        response.mustcontain('47 entries')

    def test_filter_journal_filter_on_date_2(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index',
                                    filter='date:20121020'))
        response.mustcontain('17 entries')
