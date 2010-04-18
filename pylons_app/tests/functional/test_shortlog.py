from pylons_app.tests import *

class TestShortlogController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='shortlog', action='index'))
        # Test response...
