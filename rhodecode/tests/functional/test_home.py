import time
from rhodecode.tests import *
from rhodecode.tests.fixture import Fixture
from rhodecode.model.meta import Session
from rhodecode.model.db import User, Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.repos_group import ReposGroupModel


fixture = Fixture()


class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='home', action='index'))
        #if global permission is set
        response.mustcontain('Add repository')
        # html in javascript variable:
        response.mustcontain("""var data = {"totalRecords": %s"""
                             % len(Repository.getAll()))
        response.mustcontain(r'href=\"/%s\"' % HG_REPO)

        response.mustcontain(r"""<img class=\"icon\" title=\"Mercurial repository\" """
                        r"""alt=\"Mercurial repository\" src=\"/images/icons/hg"""
                        r"""icon.png\"/>""")
        response.mustcontain(r"""<img class=\"icon\" title=\"Public repository\" """
                        r"""alt=\"Public repository\" src=\"/images/icons/lock_"""
                        r"""open.png\"/>""")

        response.mustcontain("""fixes issue with having custom format for git-log""")
        response.mustcontain("""/%s/changeset/5f2c6ee195929b0be80749243c18121c9864a3b3""" % GIT_REPO)

        response.mustcontain("""disable security checks on hg clone for travis""")
        response.mustcontain("""/%s/changeset/96507bd11ecc815ebc6270fdf6db110928c09c1e""" % HG_REPO)

    def test_repo_summary_with_anonymous_access_disabled(self):
        anon = User.get_default_user()
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
            anon = User.get_default_user()
            anon.active = True
            Session().add(anon)
            Session().commit()

    def test_index_with_anonymous_access_disabled(self):
        anon = User.get_default_user()
        anon.active = False
        Session().add(anon)
        Session().commit()
        time.sleep(1.5)  # must sleep for cache (1s to expire)
        try:
            response = self.app.get(url(controller='home', action='index'),
                                    status=302)
            assert 'login' in response.location
        finally:
            anon = User.get_default_user()
            anon.active = True
            Session().add(anon)
            Session().commit()

    def test_index_page_on_groups(self):
        self.log_user()
        gr = fixture.create_group('gr1')
        fixture.create_repo(name='gr1/repo_in_group', repos_group=gr)
        response = self.app.get(url('repos_group_home', group_name='gr1'))

        try:
            response.mustcontain("gr1/repo_in_group")
        finally:
            RepoModel().delete('gr1/repo_in_group')
            ReposGroupModel().delete(repos_group='gr1', force_delete=True)
            Session().commit()
