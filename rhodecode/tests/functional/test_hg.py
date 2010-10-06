from rhodecode.tests import *

class TestAdminController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='hg', action='index'))
        #if global permission is set
        assert 'ADD NEW REPOSITORY' in response.body, 'Wrong main page'
        assert 'href="/vcs_test/summary"' in response.body, ' mising repository in list'
        # Test response...
