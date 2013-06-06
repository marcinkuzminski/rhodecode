import datetime

from rhodecode.tests import *
from rhodecode.model.gist import GistModel
from rhodecode.model.meta import Session
from rhodecode.model.db import User, Gist


def _create_gist(f_name, content='some gist', lifetime=-1,
                 description='gist-desc', gist_type='public',
                 owner=TEST_USER_ADMIN_LOGIN):
    gist_mapping = {
        f_name: {'content': content}
    }
    user = User.get_by_username(owner)
    gist = GistModel().create(description, owner=user,
                       gist_mapping=gist_mapping, gist_type=gist_type,
                       lifetime=lifetime)
    Session().commit()
    return gist


class TestGistsController(TestController):

    def tearDown(self):
        for g in Gist.get_all():
            GistModel().delete(g)
        Session().commit()

    def test_index(self):
        self.log_user()
        response = self.app.get(url('gists'))
        # Test response...
        response.mustcontain('There are no gists yet')

        g1 = _create_gist('gist1').gist_access_id
        g2 = _create_gist('gist2', lifetime=1400).gist_access_id
        g3 = _create_gist('gist3', description='gist3-desc').gist_access_id
        g4 = _create_gist('gist4', gist_type='private').gist_access_id
        response = self.app.get(url('gists'))
        # Test response...
        response.mustcontain('gist:%s' % g1)
        response.mustcontain('gist:%s' % g2)
        response.mustcontain('Expires: in 23 hours')  # we don't care about the end
        response.mustcontain('gist:%s' % g3)
        response.mustcontain('gist3-desc')
        response.mustcontain(no=['gist:%s' % g4])

    def test_index_private_gists(self):
        self.log_user()
        gist = _create_gist('gist5', gist_type='private')
        response = self.app.get(url('gists', private=1))
        # Test response...

        #and privates
        response.mustcontain('gist:%s' % gist.gist_access_id)

    def test_create_missing_description(self):
        self.log_user()
        response = self.app.post(url('gists'),
                                 params={'lifetime': -1}, status=200)

        response.mustcontain('Missing value')

    def test_create(self):
        self.log_user()
        response = self.app.post(url('gists'),
                                 params={'lifetime': -1,
                                         'content': 'gist test',
                                         'filename': 'foo',
                                         'public': 'public'},
                                 status=302)
        response = response.follow()
        response.mustcontain('added file: foo')
        response.mustcontain('gist test')
        response.mustcontain('<div class="ui-btn green badge">Public gist</div>')

    def test_create_with_path_with_dirs(self):
        self.log_user()
        response = self.app.post(url('gists'),
                                 params={'lifetime': -1,
                                         'content': 'gist test',
                                         'filename': '/home/foo',
                                         'public': 'public'},
                                 status=200)
        response.mustcontain('Filename cannot be inside a directory')

    def test_access_expired_gist(self):
        self.log_user()
        gist = _create_gist('never-see-me')
        gist.gist_expires = 0  # 1970
        Session().add(gist)
        Session().commit()

        response = self.app.get(url('gist', gist_id=gist.gist_access_id), status=404)

    def test_create_private(self):
        self.log_user()
        response = self.app.post(url('gists'),
                                 params={'lifetime': -1,
                                         'content': 'private gist test',
                                         'filename': 'private-foo',
                                         'private': 'private'},
                                 status=302)
        response = response.follow()
        response.mustcontain('added file: private-foo<')
        response.mustcontain('private gist test')
        response.mustcontain('<div class="ui-btn yellow badge">Private gist</div>')

    def test_create_with_description(self):
        self.log_user()
        response = self.app.post(url('gists'),
                                 params={'lifetime': -1,
                                         'content': 'gist test',
                                         'filename': 'foo-desc',
                                         'description': 'gist-desc',
                                         'public': 'public'},
                                 status=302)
        response = response.follow()
        response.mustcontain('added file: foo-desc')
        response.mustcontain('gist test')
        response.mustcontain('gist-desc')
        response.mustcontain('<div class="ui-btn green badge">Public gist</div>')

    def test_new(self):
        self.log_user()
        response = self.app.get(url('new_gist'))

    def test_update(self):
        self.skipTest('not implemented')
        response = self.app.put(url('gist', gist_id=1))

    def test_delete(self):
        self.log_user()
        gist = _create_gist('delete-me')
        response = self.app.delete(url('gist', gist_id=gist.gist_id))
        self.checkSessionFlash(response, 'Deleted gist %s' % gist.gist_id)

    def test_delete_normal_user_his_gist(self):
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        gist = _create_gist('delete-me', owner=TEST_USER_REGULAR_LOGIN)
        response = self.app.delete(url('gist', gist_id=gist.gist_id))
        self.checkSessionFlash(response, 'Deleted gist %s' % gist.gist_id)

    def test_delete_normal_user_not_his_own_gist(self):
        self.log_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS)
        gist = _create_gist('delete-me')
        response = self.app.delete(url('gist', gist_id=gist.gist_id), status=403)

    def test_show(self):
        gist = _create_gist('gist-show-me')
        response = self.app.get(url('gist', gist_id=gist.gist_access_id))
        response.mustcontain('added file: gist-show-me<')
        response.mustcontain('test_admin (RhodeCode Admin) - created')
        response.mustcontain('gist-desc')
        response.mustcontain('<div class="ui-btn green badge">Public gist</div>')

    def test_show_as_raw(self):
        gist = _create_gist('gist-show-me', content='GIST CONTENT')
        response = self.app.get(url('formatted_gist',
                                    gist_id=gist.gist_access_id, format='raw'))
        self.assertEqual(response.body, 'GIST CONTENT')

    def test_show_as_raw_individual_file(self):
        gist = _create_gist('gist-show-me-raw', content='GIST BODY')
        response = self.app.get(url('formatted_gist_file',
                                    gist_id=gist.gist_access_id, format='raw',
                                    revision='tip', f_path='gist-show-me-raw'))
        self.assertEqual(response.body, 'GIST BODY')

    def test_edit(self):
        self.skipTest('not implemented')
        response = self.app.get(url('edit_gist', gist_id=1))
