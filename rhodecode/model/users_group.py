# -*- coding: utf-8 -*-
"""
    rhodecode.model.users_group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    user group model for RhodeCode

    :created_on: Oct 1, 2011
    :author: nvinot
    :copyright: (C) 2011-2011 Nicolas Vinot <aeris@imirhil.fr>
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import traceback

from rhodecode.model import BaseModel
from rhodecode.model.db import UserGroupMember, UserGroup,\
    UserGroupRepoToPerm, Permission, UserGroupToPerm, User, UserUserGroupToPerm,\
    UserGroupUserGroupToPerm
from rhodecode.lib.exceptions import UserGroupsAssignedException,\
    RepoGroupAssignmentError

log = logging.getLogger(__name__)


class UserGroupModel(BaseModel):

    cls = UserGroup

    def _get_user_group(self, users_group):
        return self._get_instance(UserGroup, users_group,
                                  callback=UserGroup.get_by_group_name)

    def _create_default_perms(self, user_group):
        # create default permission
        default_perm = 'usergroup.read'
        def_user = User.get_default_user()
        for p in def_user.user_perms:
            if p.permission.permission_name.startswith('usergroup.'):
                default_perm = p.permission.permission_name
                break

        user_group_to_perm = UserUserGroupToPerm()
        user_group_to_perm.permission = Permission.get_by_key(default_perm)

        user_group_to_perm.user_group = user_group
        user_group_to_perm.user_id = def_user.user_id
        return user_group_to_perm

    def _update_permissions(self, user_group, perms_new=None,
                            perms_updates=None):
        from rhodecode.lib.auth import HasUserGroupPermissionAny
        if not perms_new:
            perms_new = []
        if not perms_updates:
            perms_updates = []

        # update permissions
        for member, perm, member_type in perms_updates:
            if member_type == 'user':
                # this updates existing one
                self.grant_user_permission(
                    user_group=user_group, user=member, perm=perm
                )
            else:
                #check if we have permissions to alter this usergroup
                if HasUserGroupPermissionAny('usergroup.read', 'usergroup.write',
                                             'usergroup.admin')(member):
                    self.grant_users_group_permission(
                        target_user_group=user_group, user_group=member, perm=perm
                    )
        # set new permissions
        for member, perm, member_type in perms_new:
            if member_type == 'user':
                self.grant_user_permission(
                    user_group=user_group, user=member, perm=perm
                )
            else:
                #check if we have permissions to alter this usergroup
                if HasUserGroupPermissionAny('usergroup.read', 'usergroup.write',
                                             'usergroup.admin')(member):
                    self.grant_users_group_permission(
                        target_user_group=user_group, user_group=member, perm=perm
                    )

    def get(self, users_group_id, cache=False):
        return UserGroup.get(users_group_id)

    def get_group(self, users_group):
        return self._get_user_group(users_group)

    def get_by_name(self, name, cache=False, case_insensitive=False):
        return UserGroup.get_by_group_name(name, cache, case_insensitive)

    def create(self, name, owner, active=True):
        try:
            new_user_group = UserGroup()
            new_user_group.user = self._get_user(owner)
            new_user_group.users_group_name = name
            new_user_group.users_group_active = active
            self.sa.add(new_user_group)
            perm_obj = self._create_default_perms(new_user_group)
            self.sa.add(perm_obj)

            self.grant_user_permission(user_group=new_user_group,
                                       user=owner, perm='usergroup.admin')

            return new_user_group
        except Exception:
            log.error(traceback.format_exc())
            raise

    def update(self, users_group, form_data):

        try:
            users_group = self._get_user_group(users_group)

            for k, v in form_data.items():
                if k == 'users_group_members':
                    users_group.members = []
                    self.sa.flush()
                    members_list = []
                    if v:
                        v = [v] if isinstance(v, basestring) else v
                        for u_id in set(v):
                            member = UserGroupMember(users_group.users_group_id, u_id)
                            members_list.append(member)
                    setattr(users_group, 'members', members_list)
                setattr(users_group, k, v)

            self.sa.add(users_group)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def delete(self, users_group, force=False):
        """
        Deletes repository group, unless force flag is used
        raises exception if there are members in that group, else deletes
        group and users

        :param users_group:
        :param force:
        """
        try:
            users_group = self._get_user_group(users_group)

            # check if this group is not assigned to repo
            assigned_groups = UserGroupRepoToPerm.query()\
                .filter(UserGroupRepoToPerm.users_group == users_group).all()

            if assigned_groups and not force:
                raise UserGroupsAssignedException('RepoGroup assigned to %s' %
                                                   assigned_groups)

            self.sa.delete(users_group)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def add_user_to_group(self, users_group, user):
        users_group = self._get_user_group(users_group)
        user = self._get_user(user)

        for m in users_group.members:
            u = m.user
            if u.user_id == user.user_id:
                return True

        try:
            users_group_member = UserGroupMember()
            users_group_member.user = user
            users_group_member.users_group = users_group

            users_group.members.append(users_group_member)
            user.group_member.append(users_group_member)

            self.sa.add(users_group_member)
            return users_group_member
        except Exception:
            log.error(traceback.format_exc())
            raise

    def remove_user_from_group(self, users_group, user):
        users_group = self._get_user_group(users_group)
        user = self._get_user(user)

        users_group_member = None
        for m in users_group.members:
            if m.user.user_id == user.user_id:
                # Found this user's membership row
                users_group_member = m
                break

        if users_group_member:
            try:
                self.sa.delete(users_group_member)
                return True
            except Exception:
                log.error(traceback.format_exc())
                raise
        else:
            # User isn't in that group
            return False

    def has_perm(self, users_group, perm):
        users_group = self._get_user_group(users_group)
        perm = self._get_perm(perm)

        return UserGroupToPerm.query()\
            .filter(UserGroupToPerm.users_group == users_group)\
            .filter(UserGroupToPerm.permission == perm).scalar() is not None

    def grant_perm(self, users_group, perm):
        users_group = self._get_user_group(users_group)
        perm = self._get_perm(perm)

        # if this permission is already granted skip it
        _perm = UserGroupToPerm.query()\
            .filter(UserGroupToPerm.users_group == users_group)\
            .filter(UserGroupToPerm.permission == perm)\
            .scalar()
        if _perm:
            return

        new = UserGroupToPerm()
        new.users_group = users_group
        new.permission = perm
        self.sa.add(new)

    def revoke_perm(self, users_group, perm):
        users_group = self._get_user_group(users_group)
        perm = self._get_perm(perm)

        obj = UserGroupToPerm.query()\
            .filter(UserGroupToPerm.users_group == users_group)\
            .filter(UserGroupToPerm.permission == perm).scalar()
        if obj:
            self.sa.delete(obj)

    def grant_user_permission(self, user_group, user, perm):
        """
        Grant permission for user on given user group, or update
        existing one if found

        :param user_group: Instance of UserGroup, users_group_id,
            or users_group_name
        :param user: Instance of User, user_id or username
        :param perm: Instance of Permission, or permission_name
        """

        user_group = self._get_user_group(user_group)
        user = self._get_user(user)
        permission = self._get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UserUserGroupToPerm)\
            .filter(UserUserGroupToPerm.user == user)\
            .filter(UserUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj is None:
            # create new !
            obj = UserUserGroupToPerm()
        obj.user_group = user_group
        obj.user = user
        obj.permission = permission
        self.sa.add(obj)
        log.debug('Granted perm %s to %s on %s' % (perm, user, user_group))

    def revoke_user_permission(self, user_group, user):
        """
        Revoke permission for user on given repository group

        :param user_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param user: Instance of User, user_id or username
        """

        user_group = self._get_user_group(user_group)
        user = self._get_user(user)

        obj = self.sa.query(UserUserGroupToPerm)\
            .filter(UserUserGroupToPerm.user == user)\
            .filter(UserUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm on %s on %s' % (user_group, user))

    def grant_users_group_permission(self, target_user_group, user_group, perm):
        """
        Grant user group permission for given target_user_group

        :param target_user_group:
        :param user_group:
        :param perm:
        """
        target_user_group = self._get_user_group(target_user_group)
        user_group = self._get_user_group(user_group)
        permission = self._get_perm(perm)
        # forbid assigning same user group to itself
        if target_user_group == user_group:
            raise RepoGroupAssignmentError('target repo:%s cannot be '
                                           'assigned to itself' % target_user_group)

        # check if we have that permission already
        obj = self.sa.query(UserGroupUserGroupToPerm)\
            .filter(UserGroupUserGroupToPerm.target_user_group == target_user_group)\
            .filter(UserGroupUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj is None:
            # create new !
            obj = UserGroupUserGroupToPerm()
        obj.user_group = user_group
        obj.target_user_group = target_user_group
        obj.permission = permission
        self.sa.add(obj)
        log.debug('Granted perm %s to %s on %s' % (perm, target_user_group, user_group))

    def revoke_users_group_permission(self, target_user_group, user_group):
        """
        Revoke user group permission for given target_user_group

        :param target_user_group:
        :param user_group:
        """
        target_user_group = self._get_user_group(target_user_group)
        user_group = self._get_user_group(user_group)

        obj = self.sa.query(UserGroupUserGroupToPerm)\
            .filter(UserGroupUserGroupToPerm.target_user_group == target_user_group)\
            .filter(UserGroupUserGroupToPerm.user_group == user_group)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm on %s on %s' % (target_user_group, user_group))
