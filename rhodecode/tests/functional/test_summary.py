from rhodecode.tests import *
from rhodecode.model.db import Repository
from rhodecode.lib.utils import invalidate_cache

class TestSummaryController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='summary', action='index', repo_name=HG_REPO))

        #repo type
        assert """<img style="margin-bottom:2px" class="icon" title="Mercurial repository" alt="Mercurial repository" src="/images/icons/hgicon.png"/>""" in response.body
        assert """<img style="margin-bottom:2px" class="icon" title="public repository" alt="public repository" src="/images/icons/lock_open.png"/>""" in response.body

        #codes stats


        self._enable_stats()
        invalidate_cache('get_repo_cached_%s' % HG_REPO)
        response = self.app.get(url(controller='summary', action='index', repo_name=HG_REPO))
        assert """var data = {"Python": 42, "Rst": 11, "Bash": 2, "Makefile": 1, "Batch": 1, "Ini": 1, "Css": 1};""" in response.body, 'wrong info about % of codes stats'

        # clone url...
        assert """<input type="text" id="clone_url" readonly="readonly" value="hg clone http://test_admin@localhost:80/%s" size="70"/>""" % HG_REPO in response.body


    def _enable_stats(self):
        r = Repository.by_repo_name(HG_REPO)
        r.enable_statistics = True
        self.sa.add(r)
        self.sa.commit()

