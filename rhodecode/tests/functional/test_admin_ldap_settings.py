from rhodecode.tests import *

class TestLdapSettingsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='admin/ldap_settings', action='index'))
        # Test response...
