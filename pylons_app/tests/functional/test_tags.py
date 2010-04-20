from pylons_app.tests import *

class TestTagsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='tags', action='index'))
        # Test response...
