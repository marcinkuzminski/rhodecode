from rhodecode.tests import *

class TestSummaryController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='summary', action='index', repo_name='vcs_test'))
        print response
        assert """<img style="margin-bottom:2px" class="icon" title="public repository" alt="public" src="/images/icons/lock_open.png"/>""" in response.body
        
        # Test response...
