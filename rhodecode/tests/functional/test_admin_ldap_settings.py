from rhodecode.tests import *
from rhodecode.model.db import RhodeCodeSettings
from nose.plugins.skip import SkipTest

skip_ldap_test = False
try:
    import ldap
except ImportError:
    # means that python-ldap is not installed
    skip_ldap_test = True
    pass

class TestLdapSettingsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='admin/ldap_settings',
                                    action='index'))
        self.assertTrue('LDAP administration' in response.body)

    def test_ldap_save_settings(self):
        self.log_user()
        if skip_ldap_test:
            raise SkipTest('skipping due to missing ldap lib')
        
        test_url = url(controller='admin/ldap_settings',
                       action='ldap_settings')

        response = self.app.post(url=test_url,
            params={'ldap_host' : u'dc.example.com',
                    'ldap_port' : '999',
                    'ldap_tls_kind' : 'PLAIN',
                    'ldap_tls_reqcert' : 'NEVER',
                    'ldap_dn_user':'test_user',
                    'ldap_dn_pass':'test_pass',
                    'ldap_base_dn':'test_base_dn',
                    'ldap_filter':'test_filter',
                    'ldap_search_scope':'BASE',
                    'ldap_attr_login':'test_attr_login',
                    'ldap_attr_firstname':'ima',
                    'ldap_attr_lastname':'tester',
                    'ldap_attr_email':'test@example.com' })

        new_settings = RhodeCodeSettings.get_ldap_settings()
        self.assertEqual(new_settings['ldap_host'], u'dc.example.com',
                         'fail db write compare')

        self.checkSessionFlash(response,
                               'Ldap settings updated successfully')

    def test_ldap_error_form(self):
        self.log_user()
        if skip_ldap_test:
            raise SkipTest('skipping due to missing ldap lib')
                
        test_url = url(controller='admin/ldap_settings',
                       action='ldap_settings')

        response = self.app.post(url=test_url,
            params={'ldap_host' : '',
                    'ldap_port' : 'i-should-be-number',
                    'ldap_tls_kind' : 'PLAIN',
                    'ldap_tls_reqcert' : 'NEVER',
                    'ldap_dn_user':'',
                    'ldap_dn_pass':'',
                    'ldap_base_dn':'',
                    'ldap_filter':'',
                    'ldap_search_scope':'BASE',
                    'ldap_attr_login':'', #  <----- missing required input
                    'ldap_attr_firstname':'',
                    'ldap_attr_lastname':'',
                    'ldap_attr_email':'' })
        
        self.assertTrue("""<span class="error-message">The LDAP Login"""
                        """ attribute of the CN must be specified""" in
                        response.body)
        
        
        
        self.assertTrue("""<span class="error-message">Please """
                        """enter a number</span>""" in response.body)

    def test_ldap_login(self):
        pass

    def test_ldap_login_incorrect(self):
        pass
