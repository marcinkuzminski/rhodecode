from rhodecode.tests import *


class TestShortlogController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    repo_name=HG_REPO))
        # Test response...

    def test_index_git(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    repo_name=GIT_REPO))
        # Test response...
