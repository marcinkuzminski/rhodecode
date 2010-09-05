from pylons_app.tests import *

class TestFilesController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='files', action='index',
                                    repo_name='vcs_test',
                                    revision='tip',
                                    f_path='/'))
        # Test response...
