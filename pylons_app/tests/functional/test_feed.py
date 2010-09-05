from pylons_app.tests import *

class TestFeedController(TestController):

    def test_rss(self):
        response = self.app.get(url(controller='feed', action='rss',
                                    repo_name='vcs_test'))
        # Test response...

    def test_atom(self):
        response = self.app.get(url(controller='feed', action='atom',
                                    repo_name='vcs_test'))
        # Test response...