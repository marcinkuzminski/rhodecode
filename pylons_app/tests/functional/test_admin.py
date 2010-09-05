from pylons_app.tests import *

class TestAdminController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='admin/admin', action='index'))
        # Test response...
