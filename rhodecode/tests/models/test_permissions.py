import os
import unittest
from rhodecode.tests import *
from rhodecode.tests.fixture import Fixture
from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import RepoGroup, User, UserGroupRepoGroupToPerm,\
    Permission, UserToPerm
from rhodecode.model.user import UserModel

from rhodecode.model.meta import Session
from rhodecode.model.users_group import UserGroupModel
from rhodecode.lib.auth import AuthUser
from rhodecode.model.permission import PermissionModel


fixture = Fixture()


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
        self.anon = User.get_default_user()
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
            UserGroupModel().delete(self.ug1, force=True)

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
        self.g1 = fixture.create_group('test1', skip_if_exists=True)
        self.g2 = fixture.create_group('test2', skip_if_exists=True)
        u1_auth = AuthUser(user_id=self.u1.user_id)
        perms = {
            'repositories_groups': {u'test1': 'group.read', u'test2': 'group.read'},
            'global': set(Permission.DEFAULT_USER_PERMISSIONS),
            'repositories': {u'vcs_test_hg': u'repository.read'}
        }
        self.assertEqual(u1_auth.permissions['repositories'][HG_REPO],
                         perms['repositories'][HG_REPO])
        self.assertEqual(u1_auth.permissions['repositories_groups'],
                         perms['repositories_groups'])
        self.assertEqual(u1_auth.permissions['global'],
                         perms['global'])

    def test_default_admin_group_perms(self):
        self.g1 = fixture.create_group('test1', skip_if_exists=True)
        self.g2 = fixture.create_group('test2', skip_if_exists=True)
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
        self.ug1 = fixture.create_user_group('G1')
        UserGroupModel().add_user_to_group(self.ug1, self.u1)

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
        self.ug1 = fixture.create_user_group('G1')
        UserGroupModel().add_user_to_group(self.ug1, self.u3)

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
        self.ug1 = fixture.create_user_group('G1')
        # add user to group
        UserGroupModel().add_user_to_group(self.ug1, self.u1)

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
        self.g1 = fixture.create_group('group1', skip_if_exists=True)
        self.g2 = fixture.create_group('group2', skip_if_exists=True)
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
        self.test_repo = fixture.create_repo(name=name,
                                             repo_type='hg',
                                             repos_group=self.g1,
                                             cur_user=self.u1,)

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
        self.g1 = fixture.create_group('group1', skip_if_exists=True)
        a1_auth = AuthUser(user_id=self.anon.user_id)

        self.assertEqual(a1_auth.permissions['repositories_groups'],
                         {u'group1': u'group.read'})

        # set default permission to none
        ReposGroupModel().grant_user_permission(repos_group=self.g1,
                                                user=self.anon,
                                                perm='group.none')
        # make group
        self.ug1 = fixture.create_user_group('G1')
        # add user to group
        UserGroupModel().add_user_to_group(self.ug1, self.u1)
        Session().commit()

        # check if user is in the group
        membrs = [x.user_id for x in UserGroupModel().get(self.ug1.users_group_id).members]
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
        obj = Session().query(UserGroupRepoGroupToPerm)\
            .filter(UserGroupRepoGroupToPerm.group == self.g1)\
            .filter(UserGroupRepoGroupToPerm.users_group == self.ug1)\
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
                              'repository.read', 'group.read',
                              'usergroup.read']))

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
                              'repository.read', 'group.read',
                              'usergroup.read']))

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
                              'repository.read', 'group.read',
                              'usergroup.read']))

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
                              'repository.read', 'group.read',
                              'usergroup.read']))

    def test_owner_permissions_doesnot_get_overwritten_by_group(self):
        #create repo as USER,
        self.test_repo = fixture.create_repo(name='myownrepo',
                                             repo_type='hg',
                                             cur_user=self.u1)

        #he has permissions of admin as owner
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories']['myownrepo'],
                         'repository.admin')
        #set his permission as user group, he should still be admin
        self.ug1 = fixture.create_user_group('G1')
        UserGroupModel().add_user_to_group(self.ug1, self.u1)
        RepoModel().grant_users_group_permission(self.test_repo,
                                                 group_name=self.ug1,
                                                 perm='repository.none')

        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories']['myownrepo'],
                         'repository.admin')

    def test_owner_permissions_doesnot_get_overwritten_by_others(self):
        #create repo as USER,
        self.test_repo = fixture.create_repo(name='myownrepo',
                                             repo_type='hg',
                                             cur_user=self.u1)

        #he has permissions of admin as owner
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories']['myownrepo'],
                         'repository.admin')
        #set his permission as user, he should still be admin
        RepoModel().grant_user_permission(self.test_repo, user=self.u1,
                                          perm='repository.none')
        Session().commit()
        u1_auth = AuthUser(user_id=self.u1.user_id)
        self.assertEqual(u1_auth.permissions['repositories']['myownrepo'],
                         'repository.admin')

    def _test_def_perm_equal(self, user, change_factor=0):
        perms = UserToPerm.query()\
                .filter(UserToPerm.user == user)\
                .all()
        self.assertEqual(len(perms),
                         len(Permission.DEFAULT_USER_PERMISSIONS,)+change_factor,
                         msg=perms)

    def test_set_default_permissions(self):
        PermissionModel().create_default_permissions(user=self.u1)
        self._test_def_perm_equal(user=self.u1)

    def test_set_default_permissions_after_one_is_missing(self):
        PermissionModel().create_default_permissions(user=self.u1)
        self._test_def_perm_equal(user=self.u1)
        #now we delete one, it should be re-created after another call
        perms = UserToPerm.query()\
                .filter(UserToPerm.user == self.u1)\
                .all()
        Session().delete(perms[0])
        Session().commit()

        self._test_def_perm_equal(user=self.u1, change_factor=-1)

        #create missing one !
        PermissionModel().create_default_permissions(user=self.u1)
        self._test_def_perm_equal(user=self.u1)

    @parameterized.expand([
        ('repository.read', 'repository.none'),
        ('group.read', 'group.none'),
        ('usergroup.read', 'usergroup.none'),
        ('hg.create.repository', 'hg.create.none'),
        ('hg.fork.repository', 'hg.fork.none'),
        ('hg.register.manual_activate', 'hg.register.auto_activate',)
    ])
    def test_set_default_permissions_after_modification(self, perm, modify_to):
        PermissionModel().create_default_permissions(user=self.u1)
        self._test_def_perm_equal(user=self.u1)

        old = Permission.get_by_key(perm)
        new = Permission.get_by_key(modify_to)
        self.assertNotEqual(old, None)
        self.assertNotEqual(new, None)

        #now modify permissions
        p = UserToPerm.query()\
                .filter(UserToPerm.user == self.u1)\
                .filter(UserToPerm.permission == old)\
                .one()
        p.permission = new
        Session().add(p)
        Session().commit()

        PermissionModel().create_default_permissions(user=self.u1)
        self._test_def_perm_equal(user=self.u1)
