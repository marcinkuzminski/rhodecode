# -*- coding: utf-8 -*-

from rhodecode.lib.auth import get_crypt_password, check_password
from rhodecode.model.db import User, RhodeCodeSetting, Repository
from rhodecode.tests import *
from rhodecode.lib import helpers as h
from rhodecode.model.user import UserModel
from rhodecode.model.scm import ScmModel


class TestAdminSettingsController(TestController):

    def test_index(self):
        response = self.app.get(url('admin_settings'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_admin_settings', format='xml'))

    def test_create(self):
        response = self.app.post(url('admin_settings'))

    def test_new(self):
        response = self.app.get(url('admin_new_setting'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_admin_new_setting', format='xml'))

    def test_update(self):
        response = self.app.put(url('admin_setting', setting_id=1))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('admin_setting', setting_id=1), params=dict(_method='put'))

    def test_delete(self):
        response = self.app.delete(url('admin_setting', setting_id=1))

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('admin_setting', setting_id=1), params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('admin_setting', setting_id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_admin_setting', setting_id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('admin_edit_setting', setting_id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_admin_edit_setting',
                                    setting_id=1, format='xml'))

    def test_ga_code_active(self):
        self.log_user()
        old_title = 'RhodeCode'
        old_realm = 'RhodeCode authentication'
        new_ga_code = 'ga-test-123456789'
        response = self.app.post(url('admin_setting', setting_id='global'),
                                     params=dict(
                                                 _method='put',
                                                 rhodecode_title=old_title,
                                                 rhodecode_realm=old_realm,
                                                 rhodecode_ga_code=new_ga_code
                                                 ))

        self.checkSessionFlash(response, 'Updated application settings')

        self.assertEqual(RhodeCodeSetting
                         .get_app_settings()['rhodecode_ga_code'], new_ga_code)

        response = response.follow()
        response.mustcontain("""_gaq.push(['_setAccount', '%s']);""" % new_ga_code)

    def test_ga_code_inactive(self):
        self.log_user()
        old_title = 'RhodeCode'
        old_realm = 'RhodeCode authentication'
        new_ga_code = ''
        response = self.app.post(url('admin_setting', setting_id='global'),
                                     params=dict(
                                                 _method='put',
                                                 rhodecode_title=old_title,
                                                 rhodecode_realm=old_realm,
                                                 rhodecode_ga_code=new_ga_code
                                                 ))

        self.assertTrue('Updated application settings' in
                        response.session['flash'][0][1])
        self.assertEqual(RhodeCodeSetting
                        .get_app_settings()['rhodecode_ga_code'], new_ga_code)

        response = response.follow()
        self.assertFalse("""_gaq.push(['_setAccount', '%s']);""" % new_ga_code
                         in response.body)

    def test_title_change(self):
        self.log_user()
        old_title = 'RhodeCode'
        new_title = old_title + '_changed'
        old_realm = 'RhodeCode authentication'

        for new_title in ['Changed', 'Żółwik', old_title]:
            response = self.app.post(url('admin_setting', setting_id='global'),
                                         params=dict(
                                                     _method='put',
                                                     rhodecode_title=new_title,
                                                     rhodecode_realm=old_realm,
                                                     rhodecode_ga_code=''
                                                     ))

            self.checkSessionFlash(response, 'Updated application settings')
            self.assertEqual(RhodeCodeSetting
                             .get_app_settings()['rhodecode_title'],
                             new_title.decode('utf-8'))

            response = response.follow()
            response.mustcontain("""<h1><a href="/">%s</a></h1>""" % new_title)

    def test_my_account(self):
        self.log_user()
        response = self.app.get(url('admin_settings_my_account'))

        self.assertTrue('value="test_admin' in response.body)

    @parameterized.expand([('firstname', 'new_username'),
                           ('lastname', 'new_username'),
                           ('admin', True),
                           ('admin', False),
                           ('ldap_dn', 'test'),
                           ('ldap_dn', None),
                           ('active', False),
                           ('active', True),
                           ('email', 'some@email.com'),
                           ])
    def test_my_account_update(self, name, expected):
        uname = 'testme'
        usr = UserModel().create_or_update(username=uname, password='qweqwe',
                                           email='testme@rhodecod.org')
        self.Session().commit()
        params = usr.get_api_data()
        user_id = usr.user_id
        self.log_user(username=uname, password='qweqwe')
        params.update({name: expected})
        params.update({'password_confirmation': ''})
        params.update({'new_password': ''})

        try:
            response = self.app.put(url('admin_settings_my_account_update',
                                        id=user_id), params)

            self.checkSessionFlash(response,
                                   'Your account was updated successfully')

            updated_user = User.get_by_username(uname)
            updated_params = updated_user.get_api_data()
            updated_params.update({'password_confirmation': ''})
            updated_params.update({'new_password': ''})

            params['last_login'] = updated_params['last_login']
            if name == 'email':
                params['emails'] = [expected]
            if name == 'ldap_dn':
                #cannot update this via form
                params['ldap_dn'] = None
            if name == 'active':
                #my account cannot deactivate account
                params['active'] = True
            if name == 'admin':
                #my account cannot make you an admin !
                params['admin'] = False

            self.assertEqual(params, updated_params)

        finally:
            UserModel().delete('testme')

    def test_my_account_update_err_email_exists(self):
        self.log_user()

        new_email = 'test_regular@mail.com'  # already exisitn email
        response = self.app.put(url('admin_settings_my_account_update'),
                                params=dict(
                                    username='test_admin',
                                    new_password='test12',
                                    password_confirmation='test122',
                                    firstname='NewName',
                                    lastname='NewLastname',
                                    email=new_email,)
                                )

        response.mustcontain('This e-mail address is already taken')

    def test_my_account_update_err(self):
        self.log_user('test_regular2', 'test12')

        new_email = 'newmail.pl'
        response = self.app.post(url('admin_settings_my_account_update'),
                                 params=dict(
                                            _method='put',
                                            username='test_admin',
                                            new_password='test12',
                                            password_confirmation='test122',
                                            firstname='NewName',
                                            lastname='NewLastname',
                                            email=new_email,)
                                 )

        response.mustcontain('An email address must contain a single @')
        from rhodecode.model import validators
        msg = validators.ValidUsername(edit=False,
                                    old_data={})._messages['username_exists']
        msg = h.html_escape(msg % {'username': 'test_admin'})
        response.mustcontain(u"%s" % msg)

    def test_set_repo_fork_has_no_self_id(self):
        self.log_user()
        repo = Repository.get_by_repo_name(HG_REPO)
        response = self.app.get(url('edit_repo', repo_name=HG_REPO))
        opt = """<option value="%s">vcs_test_git</option>""" % repo.repo_id
        assert opt not in response.body

    def test_set_fork_of_repo(self):
        self.log_user()
        repo = Repository.get_by_repo_name(HG_REPO)
        repo2 = Repository.get_by_repo_name(GIT_REPO)
        response = self.app.put(url('repo_as_fork', repo_name=HG_REPO),
                                 params=dict(
                                    id_fork_of=repo2.repo_id
                                 ))
        repo = Repository.get_by_repo_name(HG_REPO)
        repo2 = Repository.get_by_repo_name(GIT_REPO)
        self.checkSessionFlash(response,
        'Marked repo %s as fork of %s' % (repo.repo_name, repo2.repo_name))

        assert repo.fork == repo2
        response = response.follow()
        # check if given repo is selected

        opt = """<option value="%s" selected="selected">%s</option>""" % (
                                                repo2.repo_id, repo2.repo_name)
        response.mustcontain(opt)

        # clean session flash
        #response = self.app.get(url('edit_repo', repo_name=HG_REPO))

        ## mark it as None
        response = self.app.put(url('repo_as_fork', repo_name=HG_REPO),
                                 params=dict(
                                    id_fork_of=None
                                 ))
        repo = Repository.get_by_repo_name(HG_REPO)
        repo2 = Repository.get_by_repo_name(GIT_REPO)
        self.checkSessionFlash(response,
        'Marked repo %s as fork of %s' % (repo.repo_name, "Nothing"))
        assert repo.fork == None

    def test_set_fork_of_same_repo(self):
        self.log_user()
        repo = Repository.get_by_repo_name(HG_REPO)
        response = self.app.put(url('repo_as_fork', repo_name=HG_REPO),
                                 params=dict(
                                    id_fork_of=repo.repo_id
                                 ))
        self.checkSessionFlash(response,
                               'An error occurred during this operation')