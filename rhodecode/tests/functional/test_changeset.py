from rhodecode.tests import *

class TestChangesetController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='changeset', action='index',
                                    repo_name=HG_REPO,revision='tip'))
        # Test response...
