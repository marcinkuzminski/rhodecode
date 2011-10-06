from rhodecode.tests import *

class TestReposGroupsController(TestController):

    def test_index(self):
        response = self.app.get(url('repos_groups'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_repos_groups', format='xml'))

    def test_create(self):
        response = self.app.post(url('repos_groups'))

    def test_new(self):
        response = self.app.get(url('new_repos_group'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_repos_group', format='xml'))

    def test_update(self):
        response = self.app.put(url('repos_group', id=1))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('repos_group', id=1), params=dict(_method='put'))

    def test_delete(self):
        response = self.app.delete(url('repos_group', id=1))

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('repos_group', id=1), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('repos_group', id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_repos_group', id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_repos_group', id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_repos_group', id=1, format='xml'))
