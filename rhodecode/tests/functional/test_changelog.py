from rhodecode.tests import *

class TestChangelogController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index', repo_name='vcs_test'))

        assert """<div id="chg_20" class="container">""" in response.body, 'wrong info about number of changes'
        assert """Small update at simplevcs app""" in response.body, 'missing info about commit message'
        assert """<span class="removed" title="removed">0</span>""" in response.body, 'wrong info about removed nodes'
        assert """<span class="changed" title="changed">2</span>""" in response.body, 'wrong info about changed nodes'
        assert """<span class="added" title="added">1</span>""" in response.body, 'wrong info about added nodes'

        #pagination

        response = self.app.get(url(controller='changelog', action='index', repo_name='vcs_test'), {'page':1})
        response = self.app.get(url(controller='changelog', action='index', repo_name='vcs_test'), {'page':2})
        response = self.app.get(url(controller='changelog', action='index', repo_name='vcs_test'), {'page':3})
        response = self.app.get(url(controller='changelog', action='index', repo_name='vcs_test'), {'page':4})
        response = self.app.get(url(controller='changelog', action='index', repo_name='vcs_test'), {'page':5})
        response = self.app.get(url(controller='changelog', action='index', repo_name='vcs_test'), {'page':6})
        # Test response after pagination...

        assert """<span class="removed" title="removed">20</span>"""in response.body, 'wrong info about number of removed'
        assert """<span class="changed" title="changed">1</span>"""in response.body, 'wrong info about number of changes'
        assert """<span class="added" title="added">0</span>"""in response.body, 'wrong info about number of added'
        assert """<div class="date">commit 64: 46ad32a4f974@2010-04-20 00:33:21</div>"""in response.body, 'wrong info about commit 64'

        assert """<div class="message"><a href="/vcs_test/changeset/46ad32a4f974">Merge with 2e6a2bf9356ca56df08807f4ad86d480da72a8f4</a></div>"""in response.body, 'wrong info about commit 64 is a merge'
