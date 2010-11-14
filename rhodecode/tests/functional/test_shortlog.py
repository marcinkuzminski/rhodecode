from rhodecode.tests import *

class TestShortlogController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',repo_name=HG_REPO))
        # Test response...
