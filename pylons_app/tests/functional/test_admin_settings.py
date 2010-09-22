from pylons_app.tests import *
from pylons_app.model.db import User

class TestSettingsController(TestController):

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
        response = self.app.get(url('formatted_admin_edit_setting', setting_id=1, format='xml'))

    def test_my_account(self):
        self.log_user()
        response = self.app.get(url('admin_settings_my_account'))
        print response
        assert 'value="test_admin' in response.body
        
        
            
    def test_my_account_update(self):
        self.log_user()
        new_email = 'new@mail.pl'
        response = self.app.post(url('admin_settings_my_account_update'), params=dict(
                                                            _method='put',
                                                            username='test_admin',
                                                            new_password='test',
                                                            password='',
                                                            name='NewName',
                                                            lastname='NewLastname',
                                                            email=new_email,))
        response.follow()
        print response
    
        print 'x' * 100
        print response.session
        assert 'Your account was updated succesfully' in response.session['flash'][0][1], 'no flash message about success of change'
        user = self.sa.query(User).filter(User.username == 'test_admin').one()
        assert user.email == new_email , 'incorrect user email after update got %s vs %s' % (user.email, new_email)
    
    def test_my_account_update_own_email_ok(self):
        self.log_user()
                
        new_email = 'new@mail.pl'
        response = self.app.post(url('admin_settings_my_account_update'), params=dict(
                                                            _method='put',
                                                            username='test_admin',
                                                            new_password='test',
                                                            name='NewName',
                                                            lastname='NewLastname',
                                                            email=new_email,))
        print response
                
    def test_my_account_update_err_email_exists(self):
        self.log_user()
                
        new_email = 'test_regular@mail.com'#already exisitn email
        response = self.app.post(url('admin_settings_my_account_update'), params=dict(
                                                            _method='put',
                                                            username='test_admin',
                                                            new_password='test',
                                                            name='NewName',
                                                            lastname='NewLastname',
                                                            email=new_email,))
        print response
        
        assert 'That e-mail address is already taken' in response.body, 'Missing error message about existing email'
        
        
    def test_my_account_update_err(self):
        self.log_user()
                
        new_email = 'newmail.pl'
        response = self.app.post(url('admin_settings_my_account_update'), params=dict(
                                                            _method='put',
                                                            username='test_regular2',
                                                            new_password='test',
                                                            name='NewName',
                                                            lastname='NewLastname',
                                                            email=new_email,))
        print response
        assert 'An email address must contain a single @' in response.body, 'Missing error message about wrong email'
        assert 'This username already exists' in response.body, 'Missing error message about existing user'
