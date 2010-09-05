from pylons_app.tests import *

class TestSettingsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='settings', action='index',
                                    repo_name='vcs_test'))
        # Test response...
