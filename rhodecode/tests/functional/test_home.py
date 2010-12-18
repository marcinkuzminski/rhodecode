from rhodecode.tests import *

class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='home', action='index'))
        #if global permission is set
        assert 'ADD NEW REPOSITORY' in response.body, 'Wrong main page'
        assert 'href="/%s/summary"' % HG_REPO in response.body, ' mising repository in list'
        # Test response...
