from pylons_app.tests import *

class TestFileController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='file', action='index'))
        # Test response...
