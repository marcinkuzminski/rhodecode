from rhodecode.tests import *

class TestChangelogController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO))

        assert """<div id="chg_20" class="container">""" in response.body, 'wrong info about number of changes'
        assert """Small update at simplevcs app""" in response.body, 'missing info about commit message'
        assert """<span class="removed" title="removed: ">0</span>""" in response.body, 'wrong info about removed nodes'
        assert """<span class="changed" title="changed: hg.py | models.py">2</span>""" in response.body, 'wrong info about changed nodes'
        assert """<span class="added" title="added: managers.py">1</span>""" in response.body, 'wrong info about added nodes'

        #pagination

        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':1})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':2})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':3})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':4})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':5})
        response = self.app.get(url(controller='changelog', action='index', repo_name=HG_REPO), {'page':6})

        # Test response after pagination...

        assert """<div class="date">commit 64: 46ad32a4f974@2010-04-20 00:33:21</div>"""in response.body, 'wrong info about commit 64'
        assert """<span class="removed" title="removed: api.rst">1</span>"""in response.body, 'wrong info about number of removed'
        assert """<span class="changed" title="changed: .hgignore | README.rst | conf.py | index.rst | setup.py | test_hg.py | test_nodes.py | __init__.py | __init__.py | base.py | hg.py | nodes.py | __init__.py">13</span>"""in response.body, 'wrong info about number of changes'
        assert """<span class="added" title="added: hg.rst | index.rst | index.rst | nodes.rst | index.rst | simplevcs.rst | installation.rst | quickstart.rst | setup.cfg | baseui_config.py | web.py | __init__.py | exceptions.py | __init__.py | exceptions.py | middleware.py | models.py | settings.py | utils.py | views.py">20</span>"""in response.body, 'wrong info about number of added'
        assert """<div class="message"><a href="/%s/changeset/46ad32a4f974e45472a898c6b0acb600320579b1">Merge with 2e6a2bf9356ca56df08807f4ad86d480da72a8f4</a></div>""" % HG_REPO in response.body, 'wrong info about commit 64 is a merge'



    #def test_index_git(self):
    #    self.log_user()
    #    response = self.app.get(url(controller='changelog', action='index', repo_name=GIT_REPO))
