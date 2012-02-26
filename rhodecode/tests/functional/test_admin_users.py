from rhodecode.tests import *
from rhodecode.model.db import User, Permission
from rhodecode.lib.auth import check_password
from sqlalchemy.orm.exc import NoResultFound
from rhodecode.model.user import UserModel

class TestAdminUsersController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url('users'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_users', format='xml'))

    def test_create(self):
        self.log_user()
        username = 'newtestuser'
        password = 'test12'
        password_confirmation = password
        name = 'name'
        lastname = 'lastname'
        email = 'mail@mail.com'

        response = self.app.post(url('users'),
                                 {'username':username,
                                   'password':password,
                                   'password_confirmation':password_confirmation,
                                   'name':name,
                                   'active':True,
                                   'lastname':lastname,
                                   'email':email})


        self.assertTrue('''created user %s''' % (username) in
                        response.session['flash'][0])

        new_user = self.Session.query(User).\
            filter(User.username == username).one()

        self.assertEqual(new_user.username,username)
        self.assertEqual(check_password(password, new_user.password),True)
        self.assertEqual(new_user.name,name)
        self.assertEqual(new_user.lastname,lastname)
        self.assertEqual(new_user.email,email)

        response.follow()
        response = response.follow()
        self.assertTrue("""edit">newtestuser</a>""" in response.body)

    def test_create_err(self):
        self.log_user()
        username = 'new_user'
        password = ''
        name = 'name'
        lastname = 'lastname'
        email = 'errmail.com'

        response = self.app.post(url('users'), {'username':username,
                                               'password':password,
                                               'name':name,
                                               'active':False,
                                               'lastname':lastname,
                                               'email':email})

        self.assertTrue("""<span class="error-message">Invalid username</span>""" in response.body)
        self.assertTrue("""<span class="error-message">Please enter a value</span>""" in response.body)
        self.assertTrue("""<span class="error-message">An email address must contain a single @</span>""" in response.body)

        def get_user():
            self.Session.query(User).filter(User.username == username).one()

        self.assertRaises(NoResultFound, get_user), 'found user in database'

    def test_new(self):
        self.log_user()
        response = self.app.get(url('new_user'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_user', format='xml'))

    def test_update(self):
        response = self.app.put(url('user', id=1))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('user', id=1), params=dict(_method='put'))

    def test_delete(self):
        self.log_user()
        username = 'newtestuserdeleteme'
        password = 'test12'
        name = 'name'
        lastname = 'lastname'
        email = 'todeletemail@mail.com'

        response = self.app.post(url('users'), {'username':username,
                                               'password':password,
                                               'password_confirmation':password,
                                               'name':name,
                                               'active':True,
                                               'lastname':lastname,
                                               'email':email})

        response = response.follow()

        new_user = self.Session.query(User)\
            .filter(User.username == username).one()
        response = self.app.delete(url('user', id=new_user.user_id))

        self.assertTrue("""successfully deleted user""" in
                        response.session['flash'][0])


    def test_delete_browser_fakeout(self):
        response = self.app.post(url('user', id=1),
                                 params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('user', id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_user', id=1, format='xml'))

    def test_edit(self):
        self.log_user()
        user = User.get_by_username(TEST_USER_ADMIN_LOGIN)
        response = self.app.get(url('edit_user', id=user.user_id))


    def test_add_perm_create_repo(self):
        self.log_user()
        perm_none = Permission.get_by_key('hg.create.none')
        perm_create = Permission.get_by_key('hg.create.repository')

        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)


        #User should have None permission on creation repository
        self.assertEqual(UserModel().has_perm(user, perm_none), False)
        self.assertEqual(UserModel().has_perm(user, perm_create), False)

        response = self.app.post(url('user_perm', id=user.user_id),
                                 params=dict(_method='put',
                                             create_repo_perm=True))

        perm_none = Permission.get_by_key('hg.create.none')
        perm_create = Permission.get_by_key('hg.create.repository')

        user = User.get_by_username(TEST_USER_REGULAR_LOGIN)
        #User should have None permission on creation repository
        self.assertEqual(UserModel().has_perm(user, perm_none), False)
        self.assertEqual(UserModel().has_perm(user, perm_create), True)

    def test_revoke_perm_create_repo(self):
        self.log_user()
        perm_none = Permission.get_by_key('hg.create.none')
        perm_create = Permission.get_by_key('hg.create.repository')

        user = User.get_by_username(TEST_USER_REGULAR2_LOGIN)


        #User should have None permission on creation repository
        self.assertEqual(UserModel().has_perm(user, perm_none), False)
        self.assertEqual(UserModel().has_perm(user, perm_create), False)

        response = self.app.post(url('user_perm', id=user.user_id),
                                 params=dict(_method='put'))

        perm_none = Permission.get_by_key('hg.create.none')
        perm_create = Permission.get_by_key('hg.create.repository')

        user = User.get_by_username(TEST_USER_REGULAR2_LOGIN)
        #User should have None permission on creation repository
        self.assertEqual(UserModel().has_perm(user, perm_none), True)
        self.assertEqual(UserModel().has_perm(user, perm_create), False)

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_user', id=1, format='xml'))
