from rhodecode.tests import *
from rhodecode.tests.fixture import Fixture
from rhodecode.model.db import Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.meta import Session
from rhodecode.model.scm import ScmModel

fixture = Fixture()


class TestSummaryController(TestController):

    def test_index(self):
        self.log_user()
        ID = Repository.get_by_repo_name(HG_REPO).repo_id
        response = self.app.get(url(controller='summary',
                                    action='index',
                                    repo_name=HG_REPO))

        #repo type
        response.mustcontain(
            """<img style="margin-bottom:2px" class="icon" """
            """title="Mercurial repository" alt="Mercurial repository" """
            """src="/images/icons/hgicon.png"/>"""
        )
        response.mustcontain(
            """<img style="margin-bottom:2px" class="icon" """
            """title="Public repository" alt="Public """
            """repository" src="/images/icons/lock_open.png"/>"""
        )

        #codes stats
        self._enable_stats()

        ScmModel().mark_for_invalidation(HG_REPO)
        response = self.app.get(url(controller='summary', action='index',
                                    repo_name=HG_REPO))
        response.mustcontain(
            """var data = [["py", {"count": 42, "desc": ["Python"]}], """
            """["rst", {"count": 11, "desc": ["Rst"]}], """
            """["sh", {"count": 2, "desc": ["Bash"]}], """
            """["makefile", {"count": 1, "desc": ["Makefile", "Makefile"]}],"""
            """ ["cfg", {"count": 1, "desc": ["Ini"]}], """
            """["css", {"count": 1, "desc": ["Css"]}], """
            """["bat", {"count": 1, "desc": ["Batch"]}]];"""
        )

        # clone url...
        response.mustcontain('''id="clone_url" readonly="readonly" value="http://test_admin@localhost:80/%s"''' % HG_REPO)
        response.mustcontain('''id="clone_url_id" readonly="readonly" value="http://test_admin@localhost:80/_%s"''' % ID)

    def test_index_git(self):
        self.log_user()
        ID = Repository.get_by_repo_name(GIT_REPO).repo_id
        response = self.app.get(url(controller='summary',
                                    action='index',
                                    repo_name=GIT_REPO))

        #repo type
        response.mustcontain(
            """<img style="margin-bottom:2px" class="icon" """
            """title="Git repository" alt="Git repository" """
            """src="/images/icons/giticon.png"/>"""
        )
        response.mustcontain(
            """<img style="margin-bottom:2px" class="icon" """
            """title="Public repository" alt="Public """
            """repository" src="/images/icons/lock_open.png"/>"""
        )

        # clone url...
        response.mustcontain('''id="clone_url" readonly="readonly" value="http://test_admin@localhost:80/%s"''' % GIT_REPO)
        response.mustcontain('''id="clone_url_id" readonly="readonly" value="http://test_admin@localhost:80/_%s"''' % ID)

    def test_index_by_id_hg(self):
        self.log_user()
        ID = Repository.get_by_repo_name(HG_REPO).repo_id
        response = self.app.get(url(controller='summary',
                                    action='index',
                                    repo_name='_%s' % ID))

        #repo type
        response.mustcontain("""<img style="margin-bottom:2px" class="icon" """
                        """title="Mercurial repository" alt="Mercurial """
                        """repository" src="/images/icons/hgicon.png"/>""")
        response.mustcontain("""<img style="margin-bottom:2px" class="icon" """
                        """title="Public repository" alt="Public """
                        """repository" src="/images/icons/lock_open.png"/>""")

    def test_index_by_repo_having_id_path_in_name_hg(self):
        self.log_user()
        fixture.create_repo(name='repo_1')
        response = self.app.get(url(controller='summary',
                                    action='index',
                                    repo_name='repo_1'))

        try:
            response.mustcontain("repo_1")
        finally:
            RepoModel().delete(Repository.get_by_repo_name('repo_1'))
            Session().commit()

    def test_index_by_id_git(self):
        self.log_user()
        ID = Repository.get_by_repo_name(GIT_REPO).repo_id
        response = self.app.get(url(controller='summary',
                                    action='index',
                                    repo_name='_%s' % ID))

        #repo type
        response.mustcontain("""<img style="margin-bottom:2px" class="icon" """
                        """title="Git repository" alt="Git """
                        """repository" src="/images/icons/giticon.png"/>""")
        response.mustcontain("""<img style="margin-bottom:2px" class="icon" """
                        """title="Public repository" alt="Public """
                        """repository" src="/images/icons/lock_open.png"/>""")

    def _enable_stats(self):
        r = Repository.get_by_repo_name(HG_REPO)
        r.enable_statistics = True
        self.Session.add(r)
        self.Session.commit()
