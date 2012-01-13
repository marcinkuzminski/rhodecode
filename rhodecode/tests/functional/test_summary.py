from rhodecode.tests import *
from rhodecode.model.db import Repository
from rhodecode.lib.utils import invalidate_cache


class TestSummaryController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='summary',
                                    action='index', repo_name=HG_REPO))

        #repo type
        self.assertTrue("""<img style="margin-bottom:2px" class="icon" """
                        """title="Mercurial repository" alt="Mercurial """
                        """repository" src="/images/icons/hgicon.png"/>"""
                        in response.body)
        self.assertTrue("""<img style="margin-bottom:2px" class="icon" """
                        """title="public repository" alt="public """
                        """repository" src="/images/icons/lock_open.png"/>"""
                        in response.body)

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
        response.mustcontain("""<input type="text" id="clone_url" readonly="readonly" value="hg clone http://test_admin@localhost:80/%s" size="70"/>""" % HG_REPO)

    def _enable_stats(self):
        r = Repository.get_by_repo_name(HG_REPO)
        r.enable_statistics = True
        self.sa.add(r)
        self.sa.commit()
