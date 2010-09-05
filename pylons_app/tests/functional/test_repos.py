from pylons_app.tests import *

class TestReposController(TestController):

    def test_index(self):
        response = self.app.get(url('repos'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_repos', format='xml'))

    def test_create(self):
        response = self.app.post(url('repos'))

    def test_new(self):
        response = self.app.get(url('new_repo'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_repo', format='xml'))

    def test_update(self):
        response = self.app.put(url('repo', repo_name='vcs_test'))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name='vcs_test'), params=dict(_method='put'))

    def test_delete(self):
        response = self.app.delete(url('repo', repo_name='vcs_test'))

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name='vcs_test'), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('repo', repo_name='vcs_test'))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_repo', repo_name='vcs_test', format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_repo', repo_name='vcs_test'))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_repo', repo_name='vcs_test', format='xml'))
