from rhodecode.tests import *


class TestReposGroupsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url('repos_groups'))
        response.mustcontain('There are no repository groups yet')

#    def test_index_as_xml(self):
#        response = self.app.get(url('formatted_repos_groups', format='xml'))
#
#    def test_create(self):
#        response = self.app.post(url('repos_groups'))

    def test_new(self):
        self.log_user()
        response = self.app.get(url('new_repos_group'))

    def test_new_by_regular_user(self):
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        response = self.app.get(url('new_repos_group'), status=403)
#
#    def test_new_as_xml(self):
#        response = self.app.get(url('formatted_new_repos_group', format='xml'))
#
#    def test_update(self):
#        response = self.app.put(url('repos_group', group_name=1))
#
#    def test_update_browser_fakeout(self):
#        response = self.app.post(url('repos_group', group_name=1), params=dict(_method='put'))
#
#    def test_delete(self):
#        self.log_user()
#        response = self.app.delete(url('repos_group', group_name=1))
#
#    def test_delete_browser_fakeout(self):
#        response = self.app.post(url('repos_group', group_name=1), params=dict(_method='delete'))
#
#    def test_show(self):
#        response = self.app.get(url('repos_group', group_name=1))
#
#    def test_show_as_xml(self):
#        response = self.app.get(url('formatted_repos_group', group_name=1, format='xml'))
#
#    def test_edit(self):
#        response = self.app.get(url('edit_repos_group', group_name=1))
#
#    def test_edit_as_xml(self):
#        response = self.app.get(url('formatted_edit_repos_group', group_name=1, format='xml'))
