from rhodecode.tests import *

class TestUsersGroupsController(TestController):

    def test_index(self):
        response = self.app.get(url('users_groups'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_users_groups', format='xml'))

    def test_create(self):
        response = self.app.post(url('users_groups'))

    def test_new(self):
        response = self.app.get(url('new_users_group'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_users_group', format='xml'))

    def test_update(self):
        response = self.app.put(url('users_group', id=1))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('users_group', id=1), params=dict(_method='put'))

    def test_delete(self):
        response = self.app.delete(url('users_group', id=1))

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('users_group', id=1), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('users_group', id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_users_group', id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_users_group', id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_users_group', id=1, format='xml'))
