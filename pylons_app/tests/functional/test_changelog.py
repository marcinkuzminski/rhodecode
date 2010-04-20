from pylons_app.tests import *

class TestChangelogController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='changelog', action='index'))
        # Test response...
