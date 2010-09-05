from pylons_app.tests import *

class TestBranchesController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='branches', action='index',repo_name='vcs_test'))
        # Test response...
