from pylons_app.tests import *

class TestLoginController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='login', action='index'))
        assert response.status == '200 OK','Wrong response from login page'
        # Test response...

    def test_login_admin_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_admin',
                                  'password':'test'})
        assert response.status == '302 Found','Wrong response code from login'
        assert response.session['hg_app_user'].username =='test_admin','wrong logged in user'
        response = response.follow()
        assert 'auto description for vcs_test' in response.body
    
    def test_login_regular_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_regular',
                                  'password':'test'})
        assert response.status == '302 Found','Wrong response code from login'
        assert response.session['hg_app_user'].username =='test_regular','wrong logged in user'
        response = response.follow()
        assert 'auto description for vcs_test' in response.body
        assert '<a title="Admin" href="/_admin">' not in response.body
    
    def test_login_ok_came_from(self):
        test_came_from = '/_admin/users'
        response = self.app.post(url(controller='login', action='index',came_from=test_came_from),
                                 {'username':'test_admin',
                                  'password':'test'})
        assert response.status == '302 Found','Wrong response code from came from redirection'
        response = response.follow()
        
        assert response.status == '200 OK','Wrong response from login page'
        assert 'Users administration' in response.body,'No proper title in response'
        
                
    def test_login_wrong(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'error',
                                  'password':'test'})
        assert response.status == '200 OK','Wrong response from login page'
        
        assert 'invalid user name' in response.body,'No error username message in response'
        assert 'invalid password' in response.body,'No error password message in response'
        
        
        