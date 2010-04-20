from pylons_app.tests import *

class TestGraphController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='graph', action='index'))
        # Test response...
