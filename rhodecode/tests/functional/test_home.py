from rhodecode.tests import *

class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='home', action='index'))
        #if global permission is set
        assert 'ADD NEW REPOSITORY' in response.body, 'No Button for add new repository'
        assert 'href="/%s/summary"' % HG_REPO in response.body, ' mising repository in list'
        # Test response...

        assert """<img class="icon" title="Mercurial repository" alt="Mercurial repository" src="/images/icons/hgicon.png"/>""" in response.body, 'wrong info about type of repositry'
        assert """<img class="icon" title="public repository" alt="public repository" src="/images/icons/lock_open.png"/>""" in response.body, 'wrong info about repository availabilty'
        assert """<a class="tooltip" href="/vcs_test_hg/changeset/27cd5cce30c96924232dffcd24178a07ffeb5dfc" title="merge">r173:27cd5cce30c9</a>""" in response.body, 'no info about tooltip'
