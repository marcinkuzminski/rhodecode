from rhodecode.tests import *

class TestTagsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='tags', action='index',repo_name='vcs_test'))
        # Test response...
