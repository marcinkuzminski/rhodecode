from rhodecode.tests import *
from rhodecode.model.db import User
from rhodecode.lib.auth import check_password
from sqlalchemy.orm.exc import NoResultFound

class TestAdminUsersController(TestController):

    def test_index(self):
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

        response = self.app.post(url('users'), {'username':username,
                                               'password':password,
                                               'password_confirmation':password_confirmation,
                                               'name':name,
                                               'active':True,
                                               'lastname':lastname,
                                               'email':email})


        assert '''created user %s''' % (username) in response.session['flash'][0], 'No flash message about new user'

        new_user = self.sa.query(User).filter(User.username == username).one()


        assert new_user.username == username, 'wrong info about username'
        assert check_password(password, new_user.password) == True , 'wrong info about password'
        assert new_user.name == name, 'wrong info about name'
        assert new_user.lastname == lastname, 'wrong info about lastname'
        assert new_user.email == email, 'wrong info about email'


        response.follow()
        response = response.follow()
        assert """edit">newtestuser</a>""" in response.body

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

        assert """<span class="error-message">Invalid username</span>""" in response.body
        assert """<span class="error-message">Please enter a value</span>""" in response.body
        assert """<span class="error-message">An email address must contain a single @</span>""" in response.body

        def get_user():
            self.sa.query(User).filter(User.username == username).one()

        self.assertRaises(NoResultFound, get_user), 'found user in database'

    def test_new(self):
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

        new_user = self.sa.query(User).filter(User.username == username).one()
        response = self.app.delete(url('user', id=new_user.user_id))

        assert """successfully deleted user""" in response.session['flash'][0], 'No info about user deletion'


    def test_delete_browser_fakeout(self):
        response = self.app.post(url('user', id=1), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('user', id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_user', id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_user', id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_user', id=1, format='xml'))
