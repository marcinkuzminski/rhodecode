# -*- coding: utf-8 -*-

from rhodecode.lib.auth import get_crypt_password, check_password
from rhodecode.model.db import User, RhodeCodeSetting
from rhodecode.tests import *

class TestAdminSettingsController(TestController):

    def test_index(self):
        response = self.app.get(url('admin_settings'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_admin_settings', format='xml'))

    def test_create(self):
        response = self.app.post(url('admin_settings'))

    def test_new(self):
        response = self.app.get(url('admin_new_setting'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_admin_new_setting', format='xml'))

    def test_update(self):
        response = self.app.put(url('admin_setting', setting_id=1))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('admin_setting', setting_id=1), params=dict(_method='put'))

    def test_delete(self):
        response = self.app.delete(url('admin_setting', setting_id=1))

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('admin_setting', setting_id=1), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('admin_setting', setting_id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_admin_setting', setting_id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('admin_edit_setting', setting_id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_admin_edit_setting',
                                    setting_id=1, format='xml'))


    def test_ga_code_active(self):
        self.log_user()
        old_title = 'RhodeCode'
        old_realm = 'RhodeCode authentication'
        new_ga_code = 'ga-test-123456789'
        response = self.app.post(url('admin_setting', setting_id='global'),
                                     params=dict(
                                                 _method='put',
                                                 rhodecode_title=old_title,
                                                 rhodecode_realm=old_realm,
                                                 rhodecode_ga_code=new_ga_code
                                                 ))

        self.checkSessionFlash(response, 'Updated application settings')

        self.assertEqual(RhodeCodeSetting
                         .get_app_settings()['rhodecode_ga_code'], new_ga_code)

        response = response.follow()
        self.assertTrue("""_gaq.push(['_setAccount', '%s']);""" % new_ga_code
                        in response.body)

    def test_ga_code_inactive(self):
        self.log_user()
        old_title = 'RhodeCode'
        old_realm = 'RhodeCode authentication'
        new_ga_code = ''
        response = self.app.post(url('admin_setting', setting_id='global'),
                                     params=dict(
                                                 _method='put',
                                                 rhodecode_title=old_title,
                                                 rhodecode_realm=old_realm,
                                                 rhodecode_ga_code=new_ga_code
                                                 ))

        self.assertTrue('Updated application settings' in
                        response.session['flash'][0][1])
        self.assertEqual(RhodeCodeSetting
                        .get_app_settings()['rhodecode_ga_code'], new_ga_code)

        response = response.follow()
        self.assertTrue("""_gaq.push(['_setAccount', '%s']);""" % new_ga_code
                        not in response.body)


    def test_title_change(self):
        self.log_user()
        old_title = 'RhodeCode'
        new_title = old_title + '_changed'
        old_realm = 'RhodeCode authentication'

        for new_title in ['Changed', 'Żółwik', old_title]:
            response = self.app.post(url('admin_setting', setting_id='global'),
                                         params=dict(
                                                     _method='put',
                                                     rhodecode_title=new_title,
                                                     rhodecode_realm=old_realm,
                                                     rhodecode_ga_code=''
                                                     ))

            self.checkSessionFlash(response, 'Updated application settings')
            self.assertEqual(RhodeCodeSetting
                             .get_app_settings()['rhodecode_title'],
                             new_title.decode('utf-8'))

            response = response.follow()
            self.assertTrue("""<h1><a href="/">%s</a></h1>""" % new_title
                        in response.body)


    def test_my_account(self):
        self.log_user()
        response = self.app.get(url('admin_settings_my_account'))

        self.assertTrue('value="test_admin' in response.body)

    def test_my_account_update(self):
        self.log_user()

        new_email = 'new@mail.pl'
        new_name = 'NewName'
        new_lastname = 'NewLastname'
        new_password = 'test123'


        response = self.app.post(url('admin_settings_my_account_update'),
                                 params=dict(_method='put',
                                             username='test_admin',
                                             new_password=new_password,
                                             password_confirmation = new_password,
                                             password='',
                                             name=new_name,
                                             lastname=new_lastname,
                                             email=new_email,))
        response.follow()

        assert 'Your account was updated successfully' in response.session['flash'][0][1], 'no flash message about success of change'
        user = self.Session.query(User).filter(User.username == 'test_admin').one()
        assert user.email == new_email , 'incorrect user email after update got %s vs %s' % (user.email, new_email)
        assert user.name == new_name, 'updated field mismatch %s vs %s' % (user.name, new_name)
        assert user.lastname == new_lastname, 'updated field mismatch %s vs %s' % (user.lastname, new_lastname)
        assert check_password(new_password, user.password) is True, 'password field mismatch %s vs %s' % (user.password, new_password)

        #bring back the admin settings
        old_email = 'test_admin@mail.com'
        old_name = 'RhodeCode'
        old_lastname = 'Admin'
        old_password = 'test12'

        response = self.app.post(url('admin_settings_my_account_update'), params=dict(
                                                            _method='put',
                                                            username='test_admin',
                                                            new_password=old_password,
                                                            password_confirmation = old_password,
                                                            password='',
                                                            name=old_name,
                                                            lastname=old_lastname,
                                                            email=old_email,))

        response.follow()
        self.checkSessionFlash(response,
                               'Your account was updated successfully')

        user = self.Session.query(User).filter(User.username == 'test_admin').one()
        assert user.email == old_email , 'incorrect user email after update got %s vs %s' % (user.email, old_email)

        assert user.email == old_email , 'incorrect user email after update got %s vs %s' % (user.email, old_email)
        assert user.name == old_name, 'updated field mismatch %s vs %s' % (user.name, old_name)
        assert user.lastname == old_lastname, 'updated field mismatch %s vs %s' % (user.lastname, old_lastname)
        assert check_password(old_password, user.password) is True , 'password updated field mismatch %s vs %s' % (user.password, old_password)


    def test_my_account_update_err_email_exists(self):
        self.log_user()

        new_email = 'test_regular@mail.com'#already exisitn email
        response = self.app.post(url('admin_settings_my_account_update'), params=dict(
                                                            _method='put',
                                                            username='test_admin',
                                                            new_password='test12',
                                                            password_confirmation = 'test122',
                                                            name='NewName',
                                                            lastname='NewLastname',
                                                            email=new_email,))

        assert 'This e-mail address is already taken' in response.body, 'Missing error message about existing email'


    def test_my_account_update_err(self):
        self.log_user('test_regular2', 'test12')

        new_email = 'newmail.pl'
        response = self.app.post(url('admin_settings_my_account_update'), params=dict(
                                                            _method='put',
                                                            username='test_admin',
                                                            new_password='test12',
                                                            password_confirmation = 'test122',
                                                            name='NewName',
                                                            lastname='NewLastname',
                                                            email=new_email,))
        assert 'An email address must contain a single @' in response.body, 'Missing error message about wrong email'
        assert 'This username already exists' in response.body, 'Missing error message about existing user'
