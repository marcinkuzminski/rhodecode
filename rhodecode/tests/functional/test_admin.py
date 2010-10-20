from rhodecode.tests import *

class TestAdminController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='admin/admin', action='index'))
        assert 'Admin journal' in response.body, 'No proper title in dashboard'
        # Test response...
