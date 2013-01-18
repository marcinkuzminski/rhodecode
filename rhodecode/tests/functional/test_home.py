import time
from rhodecode.tests import *
from rhodecode.model.meta import Session
from rhodecode.model.db import User, RhodeCodeSetting, Repository
from rhodecode.lib.utils import set_rhodecode_config
from rhodecode.tests.models.common import _make_repo, _make_group
from rhodecode.model.repo import RepoModel
from rhodecode.model.repos_group import ReposGroupModel


class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='home', action='index'))
        #if global permission is set
        response.mustcontain('ADD REPOSITORY')
        response.mustcontain('href="/%s/summary"' % HG_REPO)

        response.mustcontain("""<img class="icon" title="Mercurial repository" """
                        """alt="Mercurial repository" src="/images/icons/hg"""
                        """icon.png"/>""")
        response.mustcontain("""<img class="icon" title="public repository" """
                        """alt="public repository" src="/images/icons/lock_"""
                        """open.png"/>""")

        response.mustcontain(
"""<a title="Marcin Kuzminski &amp;lt;marcin@python-works.com&amp;gt;:\n
merge" class="tooltip" href="/vcs_test_hg/changeset/27cd5cce30c96924232"""
"""dffcd24178a07ffeb5dfc">r173:27cd5cce30c9</a>"""
)

    def test_repo_summary_with_anonymous_access_disabled(self):
        anon = User.get_by_username('default')
        anon.active = False
        Session().add(anon)
        Session().commit()
        time.sleep(1.5)  # must sleep for cache (1s to expire)
        try:
            response = self.app.get(url(controller='summary',
                                        action='index', repo_name=HG_REPO),
                                        status=302)
            assert 'login' in response.location

        finally:
            anon = User.get_by_username('default')
            anon.active = True
            Session().add(anon)
            Session().commit()

    def test_index_with_anonymous_access_disabled(self):
        anon = User.get_by_username('default')
        anon.active = False
        Session().add(anon)
        Session().commit()
        time.sleep(1.5)  # must sleep for cache (1s to expire)
        try:
            response = self.app.get(url(controller='home', action='index'),
                                    status=302)
            assert 'login' in response.location
        finally:
            anon = User.get_by_username('default')
            anon.active = True
            Session().add(anon)
            Session().commit()

    def _set_l_dash(self, set_to):
        self.app.post(url('admin_setting', setting_id='visual'),
                      params=dict(_method='put',
                                  rhodecode_lightweight_dashboard=set_to,))

    def test_index_with_lightweight_dashboard(self):
        self.log_user()
        self._set_l_dash(True)

        try:
            response = self.app.get(url(controller='home', action='index'))
            response.mustcontain("""var data = {"totalRecords": %s""" % len(Repository.getAll()))
        finally:
            self._set_l_dash(False)

    def test_index_page_on_groups(self):
        self.log_user()
        _make_repo(name='gr1/repo_in_group', repos_group=_make_group('gr1'))
        Session().commit()
        response = self.app.get(url('repos_group_home', group_name='gr1'))

        try:
            response.mustcontain("""gr1/repo_in_group""")
        finally:
            RepoModel().delete('gr1/repo_in_group')
            ReposGroupModel().delete(repos_group='gr1', force_delete=True)
            Session().commit()

    def test_index_page_on_groups_with_lightweight_dashboard(self):
        self.log_user()
        self._set_l_dash(True)
        _make_repo(name='gr1/repo_in_group', repos_group=_make_group('gr1'))
        Session().commit()
        response = self.app.get(url('repos_group_home', group_name='gr1'))

        try:
            response.mustcontain("""gr1/repo_in_group""")
        finally:
            self._set_l_dash(False)
            RepoModel().delete('gr1/repo_in_group')
            ReposGroupModel().delete(repos_group='gr1', force_delete=True)
            Session().commit()
