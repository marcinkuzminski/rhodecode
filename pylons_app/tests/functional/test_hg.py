from pylons_app.tests import *

class TestAdminController(TestController):

    def test_index(self):
                
        response = self.app.get(url(controller='hg', action='index'))
        # Test response...