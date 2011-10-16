# -*- coding: utf-8 -*-
from rhodecode.tests import *
from rhodecode.model.db import User
from rhodecode.lib import generate_api_key
from rhodecode.lib.auth import check_password


class TestLoginController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='login', action='index'))
        self.assertEqual(response.status, '200 OK')
        # Test response...

    def test_login_admin_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_admin',
                                  'password':'test12'})
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.session['rhodecode_user'].username ,
                         'test_admin')
        response = response.follow()
        self.assertTrue('%s repository' % HG_REPO in response.body)

    def test_login_regular_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_regular',
                                  'password':'test12'})

        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response.session['rhodecode_user'].username ,
                         'test_regular')
        response = response.follow()
        self.assertTrue('%s repository' % HG_REPO in response.body)
        self.assertTrue('<a title="Admin" href="/_admin">' not in response.body)

    def test_login_ok_came_from(self):
        test_came_from = '/_admin/users'
        response = self.app.post(url(controller='login', action='index',
                                     came_from=test_came_from),
                                 {'username':'test_admin',
                                  'password':'test12'})
        self.assertEqual(response.status, '302 Found')
        response = response.follow()

        self.assertEqual(response.status, '200 OK')
        self.assertTrue('Users administration' in response.body)


    def test_login_short_password(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'test_admin',
                                  'password':'as'})
        self.assertEqual(response.status, '200 OK')

        self.assertTrue('Enter 3 characters or more' in response.body)

    def test_login_wrong_username_password(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username':'error',
                                  'password':'test12'})
        self.assertEqual(response.status , '200 OK')

        self.assertTrue('invalid user name' in response.body)
        self.assertTrue('invalid password' in response.body)

    #==========================================================================
    # REGISTRATIONS
    #==========================================================================
    def test_register(self):
        response = self.app.get(url(controller='login', action='register'))
        self.assertTrue('Sign Up to RhodeCode' in response.body)

    def test_register_err_same_username(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'test_admin',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'goodmail@domain.com',
                                             'name':'test',
                                             'lastname':'test'})

        self.assertEqual(response.status , '200 OK')
        self.assertTrue('This username already exists' in response.body)

    def test_register_err_same_email(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'test_admin_0',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'test_admin@mail.com',
                                             'name':'test',
                                             'lastname':'test'})

        self.assertEqual(response.status , '200 OK')
        assert 'This e-mail address is already taken' in response.body

    def test_register_err_same_email_case_sensitive(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'test_admin_1',
                                             'password':'test12',
                                             'password_confirmation':'test12',
                                             'email':'TesT_Admin@mail.COM',
                                             'name':'test',
                                             'lastname':'test'})
        self.assertEqual(response.status , '200 OK')
        assert 'This e-mail address is already taken' in response.body

    def test_register_err_wrong_data(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'xs',
                                             'password':'test',
                                             'password_confirmation':'test',
                                             'email':'goodmailm',
                                             'name':'test',
                                             'lastname':'test'})
        self.assertEqual(response.status , '200 OK')
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

        self.assertEqual(response.status , '200 OK')
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

        self.assertEqual(response.status , '200 OK')
        self.assertTrue('An email address must contain a single @' in response.body)
        self.assertTrue('This username already exists' in response.body)



    def test_register_special_chars(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'xxxaxn',
                                             'password':'ąćźżąśśśś',
                                             'password_confirmation':'ąćźżąśśśś',
                                             'email':'goodmailm@test.plx',
                                             'name':'test',
                                             'lastname':'test'})

        self.assertEqual(response.status , '200 OK')
        self.assertTrue('Invalid characters in password' in response.body)


    def test_register_password_mismatch(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username':'xs',
                                             'password':'123qwe',
                                             'password_confirmation':'qwe123',
                                             'email':'goodmailm@test.plxa',
                                             'name':'test',
                                             'lastname':'test'})

        self.assertEqual(response.status , '200 OK')
        assert 'Passwords do not match' in response.body

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
        self.assertEqual(response.status , '302 Found')
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
        response = self.app.get(url(controller='login',
                                    action='password_reset'))
        self.assertEqual(response.status , '200 OK')

        username = 'test_password_reset_1'
        password = 'qweqwe'
        email = 'marcin@python-works.com'
        name = 'passwd'
        lastname = 'reset'

        new = User()
        new.username = username
        new.password = password
        new.email = email
        new.name = name
        new.lastname = lastname
        new.api_key = generate_api_key(username)
        self.sa.add(new)
        self.sa.commit()

        response = self.app.post(url(controller='login',
                                     action='password_reset'),
                                 {'email':email, })

        self.checkSessionFlash(response, 'Your password reset link was sent')

        response = response.follow()

        # BAD KEY

        key = "bad"
        response = self.app.get(url(controller='login',
                                    action='password_reset_confirmation',
                                    key=key))
        self.assertEqual(response.status, '302 Found')
        self.assertTrue(response.location.endswith(url('reset_password')))

        # GOOD KEY

        key = User.get_by_username(username).api_key

        response = self.app.get(url(controller='login',
                                    action='password_reset_confirmation',
                                    key=key))
        self.assertEqual(response.status, '302 Found')
        self.assertTrue(response.location.endswith(url('login_home')))

        self.checkSessionFlash(response,
                               ('Your password reset was successful, '
                                'new password has been sent to your email'))

        response = response.follow()
