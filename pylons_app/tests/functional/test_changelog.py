from pylons_app.tests import *

class TestChangelogController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',repo_name='vcs_test'))
        # Test response...
