import time
from rhodecode.tests import *
from rhodecode.model.meta import Session
from rhodecode.model.db import User, RhodeCodeSetting, Repository
from rhodecode.lib.utils import set_rhodecode_config


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

    def test_index_with_lightweight_dashboard(self):
        self.log_user()

        def set_l_dash(set_to):
            self.app.post(url('admin_setting', setting_id='visual'),
                          params=dict(_method='put',
                                      rhodecode_lightweight_dashboard=set_to,))

        set_l_dash(True)

        try:
            response = self.app.get(url(controller='home', action='index'))
            response.mustcontain("""var data = {"totalRecords": %s""" % len(Repository.getAll()))
        finally:
            set_l_dash(False)
