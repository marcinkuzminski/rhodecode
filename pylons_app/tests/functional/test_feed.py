from pylons_app.tests import *

class TestFeedController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='feed', action='index'))
        # Test response...
