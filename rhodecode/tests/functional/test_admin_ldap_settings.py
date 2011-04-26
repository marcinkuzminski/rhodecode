from rhodecode.tests import *

class TestLdapSettingsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='admin/ldap_settings',
                                    action='index'))
        # Test response...

    def test_ldap_save_settings(self):
        pass

    def test_ldap_error_form(self):
        pass

    def test_ldap_login(self):
        pass

    def test_ldap_login_incorrect(self):
        pass
