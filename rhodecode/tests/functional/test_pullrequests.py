from rhodecode.tests import *

class TestPullrequestsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='pullrequests', action='index'))
        # Test response...
