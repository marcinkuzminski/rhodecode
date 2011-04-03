# -*- coding: utf-8 -*-
from rhodecode.tests import *
from rhodecode.model.db import User
from rhodecode.lib.auth import check_password


class TestLoginController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='login', action='index'))
        assert response.status == '200 OK', 'Wrong response from login page got %s' % response.status
        # Test response...

    def test_login_admin_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_admin',
                                  'password':'test12'})
        assert response.status == '302 Found', 'Wrong response code from login got %s' % response.status
        assert response.session['rhodecode_user'].username == 'test_admin', 'wrong logged in user'
        response = response.follow()
        assert '%s repository' % HG_REPO in response.body

    def test_login_regular_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_regular',
                                  'password':'test12'})
        print response
        assert response.status == '302 Found', 'Wrong response code from login got %s' % response.status
        assert response.session['rhodecode_user'].username == 'test_regular', 'wrong logged in user'
        response = response.follow()
        assert '%s repository' % HG_REPO in response.body
        assert '<a title="Admin" href="/_admin">' not in response.body

    def test_login_ok_came_from(self):
        test_came_from = '/_admin/users'
        response = self.app.post(url(controller='login', action='index', came_from=test_came_from),
                                 {'username':'test_admin',
                                  'password':'test12'})
        assert response.status == '302 Found', 'Wrong response code from came from redirection'
        response = response.follow()

        assert response.status == '200 OK', 'Wrong response from login page got %s' % response.status
        assert 'Users administration' in response.body, 'No proper title in response'


    def test_login_short_password(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'error',
                                  'password':'test'})
        assert response.status == '200 OK', 'Wrong response from login page'
        print response.body
        assert 'Enter 6 characters or more' in response.body, 'No error password message in response'

    def test_login_wrong_username_password(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'error',
                                  'password':'test12'})
        assert response.status == '200 OK', 'Wrong response from login page'

        assert 'invalid user name' in response.body, 'No error username message in response'
        assert 'invalid password' in response.body, 'No error password message in response'

    #==========================================================================
    # REGISTRATIONS
    #==========================================================================
    def test_register(self):
        response = self.app.get(url(controller='login', action='register'))
        assert 'Sign Up to RhodeCode' in response.body, 'wrong page for user registration'

    def test_register_err_same_username(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'test_admin',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'goodmail@domain.com',
                                             'name':'test',
                                             'lastname':'test'})

        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        assert 'This username already exists' in response.body

    def test_register_err_same_email(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'test_admin_0',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'test_admin@mail.com',
                                             'name':'test',
                                             'lastname':'test'})

        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        assert 'This e-mail address is already taken' in response.body

    def test_register_err_same_email_case_sensitive(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'test_admin_1',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'TesT_Admin@mail.COM',
                                             'name':'test',
                                             'lastname':'test'})
        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        assert 'This e-mail address is already taken' in response.body

    def test_register_err_wrong_data(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'xs',
                                             'password':'test',
                                             'password_confirmation':'test',
                                             'email':'goodmailm',
                                             'name':'test',
                                             'lastname':'test'})
        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        assert 'An email address must contain a single @' in response.body
        assert 'Enter a value 6 characters long or more' in response.body


    def test_register_err_username(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'error user',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'goodmailm',
                                             'name':'test',
                                             'lastname':'test'})

        print response.body
        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        assert 'An email address must contain a single @' in response.body
        assert ('Username may only contain '
                'alphanumeric characters underscores, '
                'periods or dashes and must begin with '
                'alphanumeric character') in response.body

    def test_register_err_case_sensitive(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'Test_Admin',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'goodmailm',
                                             'name':'test',
                                             'lastname':'test'})

        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        assert 'An email address must contain a single @' in response.body
        assert 'This username already exists' in response.body



    def test_register_special_chars(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'xxxaxn',
                                             'password':'ąćźżąśśśś',
                                             'password_confirmation':'ąćźżąśśśś',
                                             'email':'goodmailm@test.plx',
                                             'name':'test',
                                             'lastname':'test'})

        print response.body
        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        assert 'Invalid characters in password' in response.body


    def test_register_password_mismatch(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'xs',
                                             'password':'123qwe',
                                             'password_confirmation':'qwe123',
                                             'email':'goodmailm@test.plxa',
                                             'name':'test',
                                             'lastname':'test'})

        assert response.status == '200 OK', 'Wrong response from register page got %s' % response.status
        print response.body
        assert 'Password do not match' in response.body

    def test_register_ok(self):
        username = 'test_regular4'
        password = 'qweqwe'
        email = 'marcin@test.com'
        name = 'testname'
        lastname = 'testlastname'

        response = self.app.post(url(controller='login', action='register'),
                                            {'username':username,
                                             'password':password,
                                             'password_confirmation':password,
                                             'email':email,
                                             'name':name,
                                             'lastname':lastname})
        assert response.status == '302 Found', 'Wrong response from register page got %s' % response.status
        assert 'You have successfully registered into rhodecode' in response.session['flash'][0], 'No flash message about user registration'

        ret = self.sa.query(User).filter(User.username == 'test_regular4').one()
        assert ret.username == username , 'field mismatch %s %s' % (ret.username, username)
        assert check_password(password, ret.password) == True , 'password mismatch'
        assert ret.email == email , 'field mismatch %s %s' % (ret.email, email)
        assert ret.name == name , 'field mismatch %s %s' % (ret.name, name)
        assert ret.lastname == lastname , 'field mismatch %s %s' % (ret.lastname, lastname)


    def test_forgot_password_wrong_mail(self):
        response = self.app.post(url(controller='login', action='password_reset'),
                                            {'email':'marcin@wrongmail.org', })

        assert "This e-mail address doesn't exist" in response.body, 'Missing error message about wrong email'

    def test_forgot_password(self):
        response = self.app.get(url(controller='login', action='password_reset'))
        assert response.status == '200 OK', 'Wrong response from login page got %s' % response.status

        username = 'test_password_reset_1'
        password = 'qweqwe'
        email = 'marcin@python-works.com'
        name = 'passwd'
        lastname = 'reset'

        response = self.app.post(url(controller='login', action='register'),
                                            {'username':username,
                                             'password':password,
                                             'password_confirmation':password,
                                             'email':email,
                                             'name':name,
                                             'lastname':lastname})
        #register new user for email test
        response = self.app.post(url(controller='login', action='password_reset'),
                                            {'email':email, })
        print response.session['flash']
        assert 'You have successfully registered into rhodecode' in response.session['flash'][0], 'No flash message about user registration'
        assert 'Your new password was sent' in response.session['flash'][1], 'No flash message about password reset'
