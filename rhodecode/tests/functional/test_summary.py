from rhodecode.tests import *
from rhodecode.model.db import Repository
from rhodecode.lib.utils import invalidate_cache


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
            """title="Mercurial repository" alt="Mercurial """
            """repository" src="/images/icons/hgicon.png"/>"""
        )
        response.mustcontain(
            """<img style="margin-bottom:2px" class="icon" """
            """title="public repository" alt="public """
            """repository" src="/images/icons/lock_open.png"/>"""
        )

        #codes stats
        self._enable_stats()

        invalidate_cache('get_repo_cached_%s' % HG_REPO)
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
        response.mustcontain("""<input style="width:80%;margin-left:105px" type="text" id="clone_url" readonly="readonly" value="http://test_admin@localhost:80/vcs_test_hg"/>""")
        response.mustcontain("""<input style="display:none;width:80%;margin-left:105px" type="text" id="clone_url_id" readonly="readonly" value="http://test_admin@localhost:80/_1"/>""")

    def test_index_by_id(self):
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
                        """title="public repository" alt="public """
                        """repository" src="/images/icons/lock_open.png"/>""")

    def _enable_stats(self):
        r = Repository.get_by_repo_name(HG_REPO)
        r.enable_statistics = True
        self.Session.add(r)
        self.Session.commit()
