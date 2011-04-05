from rhodecode.tests import *

class TestChangelogController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO))

        print response.body
        assert """<div id="chg_20" class="container">""" in response.body, 'wrong info about number of changes'
        assert """<div class="date">commit 154: 5e204e7583b9@2010-08-10 01:18:46</div>""" in response.body , 'no info on this commit'
        assert """Small update at simplevcs app""" in response.body, 'missing info about commit message'
        assert """<span class="removed tooltip" title="removed: No Files">0</span>""" in response.body, 'wrong info about removed nodes'
        assert """<span class="changed tooltip" title="changed: vcs/backends/hg.py<br/> vcs/web/simplevcs/models.py">2</span>""" in response.body, 'wrong info about changed nodes'
        assert """<span class="added tooltip" title="added: vcs/web/simplevcs/managers.py">1</span>""" in response.body, 'wrong info about added nodes'

        #pagination

        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':1})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':2})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':3})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':4})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':5})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':6})

        # Test response after pagination...
        print response.body
        assert """<div class="date">commit 64: 46ad32a4f974@2010-04-20 00:33:21</div>"""in response.body, 'wrong info about commit 64'
        assert """<span class="removed tooltip" title="removed: docs/api.rst">1</span>"""in response.body, 'wrong info about number of removed'
        assert """<span class="changed tooltip" title="changed: .hgignore<br/> README.rst<br/> docs/conf.py<br/> docs/index.rst<br/> setup.py<br/> tests/test_hg.py<br/> tests/test_nodes.py<br/> vcs/__init__.py<br/> vcs/backends/__init__.py<br/> vcs/backends/base.py<br/> vcs/backends/hg.py<br/> vcs/nodes.py<br/> vcs/utils/__init__.py">13</span>"""in response.body, 'wrong info about number of changes'
        assert """<span class="added tooltip" title="added: docs/api/backends/hg.rst<br/> docs/api/backends/index.rst<br/> docs/api/index.rst<br/> docs/api/nodes.rst<br/> docs/api/web/index.rst<br/> docs/api/web/simplevcs.rst<br/> docs/installation.rst<br/> docs/quickstart.rst<br/> setup.cfg<br/> vcs/utils/baseui_config.py<br/> vcs/utils/web.py<br/> vcs/web/__init__.py<br/> vcs/web/exceptions.py<br/> vcs/web/simplevcs/__init__.py<br/> vcs/web/simplevcs/exceptions.py<br/> vcs/web/simplevcs/middleware.py<br/> vcs/web/simplevcs/models.py<br/> vcs/web/simplevcs/settings.py<br/> vcs/web/simplevcs/utils.py<br/> vcs/web/simplevcs/views.py">20</span>"""in response.body, 'wrong info about number of added'
        assert """<div class="message"><a href="/%s/changeset/46ad32a4f974e45472a898c6b0acb600320579b1">Merge with 2e6a2bf9356ca56df08807f4ad86d480da72a8f4</a></div>""" % HG_REPO in response.body, 'wrong info about commit 64 is a merge'



    #def test_index_git(self):
    #    self.log_user()
    #    response = self.app.get(url(controller='changelog', action='index', repo_name=GIT_REPO))
