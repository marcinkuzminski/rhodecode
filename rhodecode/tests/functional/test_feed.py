from rhodecode.tests import *

class TestFeedController(TestController):

    def test_rss(self):
        self.log_user()
        response = self.app.get(url(controller='feed', action='rss',
                                    repo_name=HG_REPO))
        # Test response...

    def test_atom(self):
        self.log_user()
        response = self.app.get(url(controller='feed', action='atom',
                                    repo_name=HG_REPO))
        # Test response...