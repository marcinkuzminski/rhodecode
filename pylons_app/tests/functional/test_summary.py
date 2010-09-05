from pylons_app.tests import *

class TestSummaryController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='summary', action='index',repo_name='vcs_test'))
        # Test response...
