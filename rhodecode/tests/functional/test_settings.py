from rhodecode.model.db import Repository
from rhodecode.tests import *

class TestSettingsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='settings', action='index',
                                    repo_name=HG_REPO))
        # Test response...
