# -*- coding: utf-8 -*-
import unittest
import formencode

from rhodecode.tests import *

from rhodecode.model import validators as v
from rhodecode.model.users_group import UsersGroupModel

from rhodecode.model.meta import Session
from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.config.routing import ADMIN_PREFIX


class TestReposGroups(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Message_extractor(self):
        validator = v.ValidUsername()
        self.assertRaises(formencode.Invalid, validator.to_python, 'default')

        class StateObj(object):
            pass

        self.assertRaises(formencode.Invalid,
                          validator.to_python, 'default', StateObj)

    def test_ValidUsername(self):
        validator = v.ValidUsername()

        self.assertRaises(formencode.Invalid, validator.to_python, 'default')
        self.assertRaises(formencode.Invalid, validator.to_python, 'new_user')
        self.assertRaises(formencode.Invalid, validator.to_python, '.,')
        self.assertRaises(formencode.Invalid, validator.to_python,
                          TEST_USER_ADMIN_LOGIN)
        self.assertEqual('test', validator.to_python('test'))

        validator = v.ValidUsername(edit=True, old_data={'user_id': 1})

    def test_ValidRepoUser(self):
        validator = v.ValidRepoUser()
        self.assertRaises(formencode.Invalid, validator.to_python, 'nouser')
        self.assertEqual(TEST_USER_ADMIN_LOGIN,
                         validator.to_python(TEST_USER_ADMIN_LOGIN))

    def test_ValidUsersGroup(self):
        validator = v.ValidUsersGroup()
        self.assertRaises(formencode.Invalid, validator.to_python, 'default')
        self.assertRaises(formencode.Invalid, validator.to_python, '.,')

        gr = UsersGroupModel().create('test')
        gr2 = UsersGroupModel().create('tes2')
        Session.commit()
        self.assertRaises(formencode.Invalid, validator.to_python, 'test')
        assert gr.users_group_id != None
        validator = v.ValidUsersGroup(edit=True,
                                    old_data={'users_group_id':
                                              gr2.users_group_id})

        self.assertRaises(formencode.Invalid, validator.to_python, 'test')
        self.assertRaises(formencode.Invalid, validator.to_python, 'TesT')
        self.assertRaises(formencode.Invalid, validator.to_python, 'TEST')
        UsersGroupModel().delete(gr)
        UsersGroupModel().delete(gr2)
        Session.commit()

    def test_ValidReposGroup(self):
        validator = v.ValidReposGroup()
        model = ReposGroupModel()
        self.assertRaises(formencode.Invalid, validator.to_python,
                          {'group_name': HG_REPO, })
        gr = model.create(group_name='test_gr', group_description='desc',
                          parent=None,
                          just_db=True)
        self.assertRaises(formencode.Invalid,
                          validator.to_python, {'group_name': gr.group_name, })

        validator = v.ValidReposGroup(edit=True,
                                      old_data={'group_id':  gr.group_id})
        self.assertRaises(formencode.Invalid,
                          validator.to_python, {
                                        'group_name': gr.group_name + 'n',
                                        'group_parent_id': gr.group_id
                                        })
        model.delete(gr)

    def test_ValidPassword(self):
        validator = v.ValidPassword()
        self.assertEqual('lol', validator.to_python('lol'))
        self.assertEqual(None, validator.to_python(None))
        self.assertRaises(formencode.Invalid, validator.to_python, 'ąćżź')

    def test_ValidPasswordsMatch(self):
        validator = v.ValidPasswordsMatch()
        self.assertRaises(formencode.Invalid,
                    validator.to_python, {'password': 'pass',
                                          'password_confirmation': 'pass2'})

        self.assertRaises(formencode.Invalid,
                    validator.to_python, {'new_password': 'pass',
                                          'password_confirmation': 'pass2'})

        self.assertEqual({'new_password': 'pass',
                          'password_confirmation': 'pass'},
                    validator.to_python({'new_password': 'pass',
                                         'password_confirmation': 'pass'}))

        self.assertEqual({'password': 'pass',
                          'password_confirmation': 'pass'},
                    validator.to_python({'password': 'pass',
                                         'password_confirmation': 'pass'}))

    def test_ValidAuth(self):
        validator = v.ValidAuth()
        valid_creds = {
            'username': TEST_USER_REGULAR2_LOGIN,
            'password': TEST_USER_REGULAR2_PASS,
        }
        invalid_creds = {
            'username': 'err',
            'password': 'err',
        }
        self.assertEqual(valid_creds, validator.to_python(valid_creds))
        self.assertRaises(formencode.Invalid,
                          validator.to_python, invalid_creds)

    def test_ValidAuthToken(self):
        validator = v.ValidAuthToken()
        # this is untestable without a threadlocal
#        self.assertRaises(formencode.Invalid,
#                          validator.to_python, 'BadToken')
        validator

    def test_ValidRepoName(self):
        validator = v.ValidRepoName()

        self.assertRaises(formencode.Invalid,
                          validator.to_python, {'repo_name': ''})

        self.assertRaises(formencode.Invalid,
                          validator.to_python, {'repo_name': HG_REPO})

        gr = ReposGroupModel().create(group_name='group_test',
                                      group_description='desc',
                                      parent=None,)
        self.assertRaises(formencode.Invalid,
                          validator.to_python, {'repo_name': gr.group_name})

        #TODO: write an error case for that ie. create a repo withinh a group
#        self.assertRaises(formencode.Invalid,
#                          validator.to_python, {'repo_name': 'some',
#                                                'repo_group': gr.group_id})

    def test_ValidForkName(self):
        # this uses ValidRepoName validator
        assert True

    @parameterized.expand([
        ('test', 'test'), ('lolz!', 'lolz'), ('  aavv', 'aavv'),
        ('ala ma kota', 'ala-ma-kota'), ('@nooo', 'nooo'),
        ('$!haha lolz !', 'haha-lolz'), ('$$$$$', ''), ('{}OK!', 'OK'),
        ('/]re po', 're-po')])
    def test_SlugifyName(self, name, expected):
        validator = v.SlugifyName()
        self.assertEqual(expected, validator.to_python(name))

    def test_ValidCloneUri(self):
            self.fail('TODO:')

    def test_ValidForkType(self):
            validator = v.ValidForkType(old_data={'repo_type': 'hg'})
            self.assertEqual('hg', validator.to_python('hg'))
            self.assertRaises(formencode.Invalid, validator.to_python, 'git')

    def test_ValidPerms(self):
            self.fail('TODO:')

    def test_ValidSettings(self):
        validator = v.ValidSettings()
        self.assertEqual({'pass': 'pass'},
                         validator.to_python(value={'user': 'test',
                                                    'pass': 'pass'}))

        self.assertEqual({'user2': 'test', 'pass': 'pass'},
                         validator.to_python(value={'user2': 'test',
                                                    'pass': 'pass'}))

    def test_ValidPath(self):
            validator = v.ValidPath()
            self.assertEqual(TESTS_TMP_PATH,
                             validator.to_python(TESTS_TMP_PATH))
            self.assertRaises(formencode.Invalid, validator.to_python,
                              '/no_such_dir')

    def test_UniqSystemEmail(self):
        validator = v.UniqSystemEmail(old_data={})

        self.assertEqual('mail@python.org',
                         validator.to_python('MaiL@Python.org'))

        email = TEST_USER_REGULAR2_EMAIL
        self.assertRaises(formencode.Invalid, validator.to_python, email)

    def test_ValidSystemEmail(self):
        validator = v.ValidSystemEmail()
        email = TEST_USER_REGULAR2_EMAIL

        self.assertEqual(email, validator.to_python(email))
        self.assertRaises(formencode.Invalid, validator.to_python, 'err')

    def test_LdapLibValidator(self):
        validator = v.LdapLibValidator()
        self.assertRaises(v.LdapImportError, validator.to_python, 'err')

    def test_AttrLoginValidator(self):
        validator = v.AttrLoginValidator()
        self.assertRaises(formencode.Invalid, validator.to_python, 123)
