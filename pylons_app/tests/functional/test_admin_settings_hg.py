from pylons_app.tests import *

class TestSettingsHgController(TestController):

    def test_index(self):
        response = self.app.get(url('admin_settings_hg'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_admin_settings_hg', format='xml'))

    def test_create(self):
        response = self.app.post(url('admin_settings_hg'))

    def test_new(self):
        response = self.app.get(url('admin_new_setting_hg'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_admin_new_setting_hg', format='xml'))

    def test_update(self):
        response = self.app.put(url('admin_setting_hg', id=1))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('admin_setting_hg', id=1), params=dict(_method='put'))

    def test_delete(self):
        response = self.app.delete(url('admin_setting_hg', id=1))

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('admin_setting_hg', id=1), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('admin_setting_hg', id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_admin_setting_hg', id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('admin_edit_setting_hg', id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_admin_edit_setting_hg', id=1, format='xml'))
