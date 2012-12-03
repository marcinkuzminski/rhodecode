from rhodecode.tests import *
from rhodecode.model.db import RhodeCodeSetting


class TestDefaultsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url('defaults'))
        response.mustcontain('default_repo_private')
        response.mustcontain('default_repo_enable_statistics')
        response.mustcontain('default_repo_enable_downloads')
        response.mustcontain('default_repo_enable_locking')

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_defaults', format='xml'))

    def test_create(self):
        response = self.app.post(url('defaults'))

    def test_new(self):
        response = self.app.get(url('new_default'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_default', format='xml'))

    def test_update(self):
        self.log_user()
        params = {
            'default_repo_enable_locking': True,
            'default_repo_enable_downloads': True,
            'default_repo_enable_statistics': True,
            'default_repo_private': True,
            'default_repo_type': 'hg',
        }
        response = self.app.put(url('default', id='default'), params=params)
        self.checkSessionFlash(response, 'Default settings updated successfully')
        defs = RhodeCodeSetting.get_default_repo_settings()
        self.assertEqual(params, defs)

        params = {
            'default_repo_enable_locking': False,
            'default_repo_enable_downloads': False,
            'default_repo_enable_statistics': False,
            'default_repo_private': False,
            'default_repo_type': 'git',
        }
        response = self.app.put(url('default', id='default'), params=params)
        self.checkSessionFlash(response, 'Default settings updated successfully')
        defs = RhodeCodeSetting.get_default_repo_settings()
        self.assertEqual(params, defs)

    def test_update_browser_fakeout(self):
        response = self.app.post(url('default', id=1), params=dict(_method='put'))

    def test_delete(self):
        response = self.app.delete(url('default', id=1))

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('default', id=1), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('default', id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_default', id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_default', id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_default', id=1, format='xml'))
