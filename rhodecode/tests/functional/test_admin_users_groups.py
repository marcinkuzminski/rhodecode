from rhodecode.tests import *
from rhodecode.model.db import UsersGroup, UsersGroupToPerm, Permission

TEST_USERS_GROUP = 'admins_test'


class TestAdminUsersGroupsController(TestController):

    def test_index(self):
        response = self.app.get(url('users_groups'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_users_groups', format='xml'))

    def test_create(self):
        self.log_user()
        users_group_name = TEST_USERS_GROUP
        response = self.app.post(url('users_groups'),
                                 {'users_group_name': users_group_name,
                                  'active':True})
        response.follow()

        self.checkSessionFlash(response,
                               'created users group %s' % TEST_USERS_GROUP)

    def test_new(self):
        response = self.app.get(url('new_users_group'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_users_group', format='xml'))

    def test_update(self):
        response = self.app.put(url('users_group', id=1))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('users_group', id=1),
                                 params=dict(_method='put'))

    def test_delete(self):
        self.log_user()
        users_group_name = TEST_USERS_GROUP + 'another'
        response = self.app.post(url('users_groups'),
                                 {'users_group_name':users_group_name,
                                  'active':True})
        response.follow()

        self.checkSessionFlash(response,
                               'created users group %s' % users_group_name)

        gr = self.Session.query(UsersGroup)\
                           .filter(UsersGroup.users_group_name ==
                                   users_group_name).one()

        response = self.app.delete(url('users_group', id=gr.users_group_id))

        gr = self.Session.query(UsersGroup)\
                           .filter(UsersGroup.users_group_name ==
                                   users_group_name).scalar()

        self.assertEqual(gr, None)

    def test_enable_repository_read_on_group(self):
        self.log_user()
        users_group_name = TEST_USERS_GROUP + 'another2'
        response = self.app.post(url('users_groups'),
                                 {'users_group_name': users_group_name,
                                  'active':True})
        response.follow()

        ug = UsersGroup.get_by_group_name(users_group_name)
        self.checkSessionFlash(response,
                               'created users group %s' % users_group_name)

        response = self.app.put(url('users_group_perm', id=ug.users_group_id),
                                 {'create_repo_perm': True})

        response.follow()
        ug = UsersGroup.get_by_group_name(users_group_name)
        p = Permission.get_by_key('hg.create.repository')
        # check if user has this perm
        perms = UsersGroupToPerm.query()\
            .filter(UsersGroupToPerm.users_group == ug).all()
        perms = [[x.__dict__['users_group_id'],
                  x.__dict__['permission_id'],] for x in perms]
        self.assertEqual(
            perms,
            [[ug.users_group_id, p.permission_id]]
        )

        # DELETE !
        ug = UsersGroup.get_by_group_name(users_group_name)
        ugid = ug.users_group_id
        response = self.app.delete(url('users_group', id=ug.users_group_id))
        response = response.follow()
        gr = self.Session.query(UsersGroup)\
                           .filter(UsersGroup.users_group_name ==
                                   users_group_name).scalar()

        self.assertEqual(gr, None)
        p = Permission.get_by_key('hg.create.repository')
        perms = UsersGroupToPerm.query()\
            .filter(UsersGroupToPerm.users_group_id == ugid).all()
        perms = [[x.__dict__['users_group_id'],
                  x.__dict__['permission_id'],] for x in perms]
        self.assertEqual(
            perms,
            []
        )

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('users_group', id=1),
                                 params=dict(_method='delete'))

    def test_show(self):
        response = self.app.get(url('users_group', id=1))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_users_group', id=1, format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_users_group', id=1))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_users_group', id=1, format='xml'))

    def test_assign_members(self):
        pass

    def test_add_create_permission(self):
        pass

    def test_revoke_members(self):
        pass
