from rhodecode.tests import *
from rhodecode.model.db import RhodeCodeSetting

class TestLdapSettingsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='admin/ldap_settings',
                                    action='index'))
        response.mustcontain('LDAP administration')

    def test_ldap_save_settings(self):
        self.log_user()
        if ldap_lib_installed:
            raise SkipTest('skipping due to missing ldap lib')

        test_url = url(controller='admin/ldap_settings',
                       action='ldap_settings')

        response = self.app.post(url=test_url,
            params={'ldap_host': u'dc.example.com',
                    'ldap_port': '999',
                    'ldap_tls_kind': 'PLAIN',
                    'ldap_tls_reqcert': 'NEVER',
                    'ldap_dn_user': 'test_user',
                    'ldap_dn_pass': 'test_pass',
                    'ldap_base_dn': 'test_base_dn',
                    'ldap_filter': 'test_filter',
                    'ldap_search_scope': 'BASE',
                    'ldap_attr_login': 'test_attr_login',
                    'ldap_attr_firstname': 'ima',
                    'ldap_attr_lastname': 'tester',
                    'ldap_attr_email': 'test@example.com' })

        new_settings = RhodeCodeSetting.get_ldap_settings()
        self.assertEqual(new_settings['ldap_host'], u'dc.example.com',
                         'fail db write compare')

        self.checkSessionFlash(response,
                               'LDAP settings updated successfully')

    def test_ldap_error_form_wrong_port_number(self):
        self.log_user()
        if ldap_lib_installed:
            raise SkipTest('skipping due to missing ldap lib')

        test_url = url(controller='admin/ldap_settings',
                       action='ldap_settings')

        response = self.app.post(url=test_url,
            params={'ldap_host': '',
                    'ldap_port': 'i-should-be-number',  # bad port num
                    'ldap_tls_kind': 'PLAIN',
                    'ldap_tls_reqcert': 'NEVER',
                    'ldap_dn_user': '',
                    'ldap_dn_pass': '',
                    'ldap_base_dn': '',
                    'ldap_filter': '',
                    'ldap_search_scope': 'BASE',
                    'ldap_attr_login': '',
                    'ldap_attr_firstname': '',
                    'ldap_attr_lastname': '',
                    'ldap_attr_email': ''})

        response.mustcontain("""<span class="error-message">"""
                             """Please enter a number</span><br />""")

    def test_ldap_error_form(self):
        self.log_user()
        if ldap_lib_installed:
            raise SkipTest('skipping due to missing ldap lib')

        test_url = url(controller='admin/ldap_settings',
                       action='ldap_settings')

        response = self.app.post(url=test_url,
            params={'ldap_host': 'Host',
                    'ldap_port': '123',
                    'ldap_tls_kind': 'PLAIN',
                    'ldap_tls_reqcert': 'NEVER',
                    'ldap_dn_user': '',
                    'ldap_dn_pass': '',
                    'ldap_base_dn': '',
                    'ldap_filter': '',
                    'ldap_search_scope': 'BASE',
                    'ldap_attr_login': '',  # <----- missing required input
                    'ldap_attr_firstname': '',
                    'ldap_attr_lastname': '',
                    'ldap_attr_email': ''})

        response.mustcontain("""<span class="error-message">The LDAP Login"""
                             """ attribute of the CN must be specified""")

    def test_ldap_login(self):
        pass

    def test_ldap_login_incorrect(self):
        pass
