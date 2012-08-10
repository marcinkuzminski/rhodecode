import os
import unittest
from rhodecode.tests import *

from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import RepoGroup, User, UsersGroupRepoGroupToPerm
from rhodecode.model.user import UserModel

from rhodecode.model.meta import Session
from rhodecode.model.users_group import UsersGroupModel
from rhodecode.lib.auth import AuthUser


def _make_group(path, desc='desc', parent_id=None,
                 skip_if_exists=False):

    gr = RepoGroup.get_by_group_name(path)
    if gr and skip_if_exists:
        return gr

    gr = ReposGroupModel().create(path, desc, parent_id)
    return gr


class TestPermissions(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super(TestPermissions, self).__init__(methodName=methodName)

    def setUp(self):
        self.u1 = UserModel().create_or_update(
            username=u'u1', password=u'qweqwe',
            email=u'u1@rhodecode.org', firstname=u'u1', lastname=u'u1'
        )
        self.u2 = UserModel().create_or_update(
            username=u'u2', password=u'qweqwe',
            email=u'u2@rhodecode.org', firstname=u'u2', lastname=u'u2'
        )
        self.u3 = UserModel().create_or_update(
            username=u'u3', password=u'qweqwe',
            email=u'u3@rhodecode.org', firstname=u'u3', lastname=u'u3'
        )
        self.anon = User.get_by_username('default')
        self.a1 = UserModel().create_or_update(
            username=u'a1', password=u'qweqwe',
            email=u'a1@rhodecode.org', firstname=u'a1', lastname=u'a1', admin=True
        )
        Session().commit()

    def tearDown(self):
        if hasattr(self, 'test_repo'):
            RepoModel().delete(repo=self.test_repo)
        UserModel().delete(self.u1)
        UserModel().delete(self.u2)
        UserModel().delete(self.u3)
        UserModel().delete(self.a1)
        if hasattr(self, 'g1'):
            ReposGroupModel().delete(self.g1.group_id)
        if hasattr(self, 'g2'):
            ReposGroupModel().delete(self.g2.group_id)

        if hasattr(self, 'ug1'):
            UsersGroupModel().delete(self.ug1, force=True)

        Session().commit()

    def test_default_perms_set(self):
        u1_auth = AuthUser(user_id=self.u1.user_id)
        perms = {
            'repositories_groups': {},
            'global': set([u'hg.create.repository', u'repository.read',
                           u'hg.register.manual_activate']),
            'repositories': {u'vcs_test_hg': u'repository.read'}
        }
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         perms['repositories'][HG_REPO])
        new_perm = 'repository.write'
        RepoModel().grant_user_permission(repo=HG_REPO, user=self.u1,
                                          perm=new_perm)
        Session().commit()

        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         new_perm)

    def test_default_admin_perms_set(self):
        a1_auth = AuthUser(user_id=self.a1.user_id)
        perms = {
            'repositories_groups': {},
            'global': set([u'hg.admin']),
            'repositories': {u'vcs_test_hg': u'repository.admin'}
        }
        self.assertEqual(a1_auth.permissions['repositories'][HG_REPO],
                         perms['repositories'][HG_REPO])
        new_perm = 'repository.write'
        RepoModel().grant_user_permission(repo=HG_REPO, user=self.a1,
                                          perm=new_perm)
        Session().commit()
        # cannot really downgrade admins permissions !? they still get's set as
        # admin !
        u1_auth = AuthUser(user_id=self.a1.user_id)
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         perms['repositories'][HG_REPO])

    def test_default_group_perms(self):
        self.g1 = _make_group('test1', skip_if_exists=True)
        self.g2 = _make_group('test2', skip_if_exists=True)
        u1_auth = AuthUser(user_id=self.u1.user_id)
        perms = {
            'repositories_groups': {u'test1': 'group.read', u'test2': 'group.read'},
            'global': set([u'hg.create.repository', u'repository.read', u'hg.register.manual_activate']),
            'repositories': {u'vcs_test_hg': u'repository.read'}
        }
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         perms['repositories'][HG_REPO])
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                         perms['repositories_groups'])

    def test_default_admin_group_perms(self):
        self.g1 = _make_group('test1', skip_if_exists=True)
        self.g2 = _make_group('test2', skip_if_exists=True)
        a1_auth = AuthUser(user_id=self.a1.user_id)
        perms = {
            'repositories_groups': {u'test1': 'group.admin', u'test2': 'group.admin'},
            'global': set(['hg.admin']),
            'repositories': {u'vcs_test_hg': 'repository.admin'}
        }

        self.assertEqual(a1_auth.permissions['repositories'][HG_REPO],
                         perms['repositories'][HG_REPO])
        self.assertEqual(a1_auth.permissions['repositories_groups'],
                         perms['repositories_groups'])

    def test_propagated_permission_from_users_group_by_explicit_perms_exist(self):
        # make group
        self.ug1 = UsersGroupModel().create('G1')
        # add user to group

        UsersGroupModel().add_user_to_group(self.ug1, self.u1)

        # set permission to lower
        new_perm = 'repository.none'
        RepoModel().grant_user_permission(repo=HG_REPO, user=self.u1, perm=new_perm)
        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         new_perm)

        # grant perm for group this should not override permission from user
        # since it has explicitly set
        new_perm_gr = 'repository.write'
        RepoModel().grant_users_group_permission(repo=HG_REPO,
                                                 group_name=self.ug1,
                                                 perm=new_perm_gr)
        # check perms
        u1_auth = AuthUser(user_id=self.u1.user_id)
        perms = {
            'repositories_groups': {},
            'global': set([u'hg.create.repository', u'repository.read',
                           u'hg.register.manual_activate']),
            'repositories': {u'vcs_test_hg': u'repository.read'}
        }
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         new_perm)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                         perms['repositories_groups'])

    def test_propagated_permission_from_users_group(self):
        # make group
        self.ug1 = UsersGroupModel().create('G1')
        # add user to group

        UsersGroupModel().add_user_to_group(self.ug1, self.u3)

        # grant perm for group this should override default permission from user
        new_perm_gr = 'repository.write'
        RepoModel().grant_users_group_permission(repo=HG_REPO,
                                                 group_name=self.ug1,
                                                 perm=new_perm_gr)
        # check perms
        u3_auth = AuthUser(user_id=self.u3.user_id)
        perms = {
            'repositories_groups': {},
            'global': set([u'hg.create.repository', u'repository.read',
                           u'hg.register.manual_activate']),
            'repositories': {u'vcs_test_hg': u'repository.read'}
        }
        self.assertEqual(u3_auth.permissions['repositories'][HG_REPO],
                         new_perm_gr)
        self.assertEqual(u3_auth.permissions['repositories_groups'],
                         perms['repositories_groups'])

    def test_propagated_permission_from_users_group_lower_weight(self):
        # make group
        self.ug1 = UsersGroupModel().create('G1')
        # add user to group
        UsersGroupModel().add_user_to_group(self.ug1, self.u1)

        # set permission to lower
        new_perm_h = 'repository.write'
        RepoModel().grant_user_permission(repo=HG_REPO, user=self.u1,
                                          perm=new_perm_h)
        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         new_perm_h)

        # grant perm for group this should NOT override permission from user
        # since it's lower than granted
        new_perm_l = 'repository.read'
        RepoModel().grant_users_group_permission(repo=HG_REPO,
                                                 group_name=self.ug1,
                                                 perm=new_perm_l)
        # check perms
        u1_auth = AuthUser(user_id=self.u1.user_id)
        perms = {
            'repositories_groups': {},
            'global': set([u'hg.create.repository', u'repository.read',
                           u'hg.register.manual_activate']),
            'repositories': {u'vcs_test_hg': u'repository.write'}
        }
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         new_perm_h)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                         perms['repositories_groups'])

    def test_repo_in_group_permissions(self):
        self.g1 = _make_group('group1', skip_if_exists=True)
        self.g2 = _make_group('group2', skip_if_exists=True)
        Session().commit()
        # both perms should be read !
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                         {u'group1': u'group.read', u'group2': u'group.read'})

        a1_auth = AuthUser(user_id=self.anon.user_id)
        self.assertEqual(a1_auth.permissions['repositories_groups'],
                 {u'group1': u'group.read', u'group2': u'group.read'})

        #Change perms to none for both groups
        ReposGroupModel().grant_user_permission(repos_group=self.g1,
                                                user=self.anon,
                                                perm='group.none')
        ReposGroupModel().grant_user_permission(repos_group=self.g2,
                                                user=self.anon,
                                                perm='group.none')

        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                 {u'group1': u'group.none', u'group2': u'group.none'})

        a1_auth = AuthUser(user_id=self.anon.user_id)
        self.assertEqual(a1_auth.permissions['repositories_groups'],
                 {u'group1': u'group.none', u'group2': u'group.none'})

        # add repo to group
        name = RepoGroup.url_sep().join([self.g1.group_name, 'test_perm'])
        self.test_repo = RepoModel().create_repo(
            repo_name=name,
            repo_type='hg',
            description='',
            repos_group=self.g1,
            owner=self.u1,
        )
        Session().commit()

        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                 {u'group1': u'group.none', u'group2': u'group.none'})

        a1_auth = AuthUser(user_id=self.anon.user_id)
        self.assertEqual(a1_auth.permissions['repositories_groups'],
                 {u'group1': u'group.none', u'group2': u'group.none'})

        #grant permission for u2 !
        ReposGroupModel().grant_user_permission(repos_group=self.g1,
                                                user=self.u2,
                                                perm='group.read')
        ReposGroupModel().grant_user_permission(repos_group=self.g2,
                                                user=self.u2,
                                                perm='group.read')
        Session().commit()
        self.assertNotEqual(self.u1, self.u2)
        #u1 and anon should have not change perms while u2 should !
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                 {u'group1': u'group.none', u'group2': u'group.none'})

        u2_auth = AuthUser(user_id=self.u2.user_id)
        self.assertEqual(u2_auth.permissions['repositories_groups'],
                 {u'group1': u'group.read', u'group2': u'group.read'})

        a1_auth = AuthUser(user_id=self.anon.user_id)
        self.assertEqual(a1_auth.permissions['repositories_groups'],
                 {u'group1': u'group.none', u'group2': u'group.none'})

    def test_repo_group_user_as_user_group_member(self):
        # create Group1
        self.g1 = _make_group('group1', skip_if_exists=True)
        Session().commit()
        a1_auth = AuthUser(user_id=self.anon.user_id)

        self.assertEqual(a1_auth.permissions['repositories_groups'],
                         {u'group1': u'group.read'})

        # set default permission to none
        ReposGroupModel().grant_user_permission(repos_group=self.g1,
                                                user=self.anon,
                                                perm='group.none')
        # make group
        self.ug1 = UsersGroupModel().create('G1')
        # add user to group
        UsersGroupModel().add_user_to_group(self.ug1, self.u1)
        Session().commit()

        # check if user is in the group
        membrs = [x.user_id for x in UsersGroupModel().get(self.ug1.users_group_id).members]
        self.assertEqual(membrs, [self.u1.user_id])
        # add some user to that group

        # check his permissions
        a1_auth = AuthUser(user_id=self.anon.user_id)
        self.assertEqual(a1_auth.permissions['repositories_groups'],
                         {u'group1': u'group.none'})

        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                         {u'group1': u'group.none'})

        # grant ug1 read permissions for
        ReposGroupModel().grant_users_group_permission(repos_group=self.g1,
                                                       group_name=self.ug1,
                                                       perm='group.read')
        Session().commit()
        # check if the
        obj = Session().query(UsersGroupRepoGroupToPerm)\
            .filter(UsersGroupRepoGroupToPerm.group == self.g1)\
            .filter(UsersGroupRepoGroupToPerm.users_group == self.ug1)\
            .scalar()
        self.assertEqual(obj.permission.permission_name, 'group.read')

        a1_auth = AuthUser(user_id=self.anon.user_id)

        self.assertEqual(a1_auth.permissions['repositories_groups'],
                         {u'group1': u'group.none'})

        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                         {u'group1': u'group.read'})

    def test_inherited_permissions_from_default_on_user_enabled(self):
        user_model = UserModel()
        # enable fork and create on default user
        usr = 'default'
        user_model.revoke_perm(usr, 'hg.create.none')
        user_model.grant_perm(usr, 'hg.create.repository')
        user_model.revoke_perm(usr, 'hg.fork.none')
        user_model.grant_perm(usr, 'hg.fork.repository')
        # make sure inherit flag is turned on
        self.u1.inherit_default_permissions = True
        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        # this user will have inherited permissions from default user
        self.assertEqual(u1_auth.permissions['global'],
                         set(['hg.create.repository', 'hg.fork.repository',
                              'hg.register.manual_activate',
                              'repository.read']))

    def test_inherited_permissions_from_default_on_user_disabled(self):
        user_model = UserModel()
        # disable fork and create on default user
        usr = 'default'
        user_model.revoke_perm(usr, 'hg.create.repository')
        user_model.grant_perm(usr, 'hg.create.none')
        user_model.revoke_perm(usr, 'hg.fork.repository')
        user_model.grant_perm(usr, 'hg.fork.none')
        # make sure inherit flag is turned on
        self.u1.inherit_default_permissions = True
        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        # this user will have inherited permissions from default user
        self.assertEqual(u1_auth.permissions['global'],
                         set(['hg.create.none', 'hg.fork.none',
                              'hg.register.manual_activate',
                              'repository.read']))

    def test_non_inherited_permissions_from_default_on_user_enabled(self):
        user_model = UserModel()
        # enable fork and create on default user
        usr = 'default'
        user_model.revoke_perm(usr, 'hg.create.none')
        user_model.grant_perm(usr, 'hg.create.repository')
        user_model.revoke_perm(usr, 'hg.fork.none')
        user_model.grant_perm(usr, 'hg.fork.repository')

        #disable global perms on specific user
        user_model.revoke_perm(self.u1, 'hg.create.repository')
        user_model.grant_perm(self.u1, 'hg.create.none')
        user_model.revoke_perm(self.u1, 'hg.fork.repository')
        user_model.grant_perm(self.u1, 'hg.fork.none')

        # make sure inherit flag is turned off
        self.u1.inherit_default_permissions = False
        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        # this user will have non inherited permissions from he's
        # explicitly set permissions
        self.assertEqual(u1_auth.permissions['global'],
                         set(['hg.create.none', 'hg.fork.none',
                              'hg.register.manual_activate',
                              'repository.read']))

    def test_non_inherited_permissions_from_default_on_user_disabled(self):
        user_model = UserModel()
        # disable fork and create on default user
        usr = 'default'
        user_model.revoke_perm(usr, 'hg.create.repository')
        user_model.grant_perm(usr, 'hg.create.none')
        user_model.revoke_perm(usr, 'hg.fork.repository')
        user_model.grant_perm(usr, 'hg.fork.none')

        #enable global perms on specific user
        user_model.revoke_perm(self.u1, 'hg.create.none')
        user_model.grant_perm(self.u1, 'hg.create.repository')
        user_model.revoke_perm(self.u1, 'hg.fork.none')
        user_model.grant_perm(self.u1, 'hg.fork.repository')

        # make sure inherit flag is turned off
        self.u1.inherit_default_permissions = False
        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        # this user will have non inherited permissions from he's
        # explicitly set permissions
        self.assertEqual(u1_auth.permissions['global'],
                         set(['hg.create.repository', 'hg.fork.repository',
                              'hg.register.manual_activate',
                              'repository.read']))

