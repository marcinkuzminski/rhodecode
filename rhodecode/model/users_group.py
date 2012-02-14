# -*- coding: utf-8 -*-
"""
    rhodecode.model.users_group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    users group model for RhodeCode

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
from rhodecode.model.db import UsersGroupMember, UsersGroup,\
    UsersGroupRepoToPerm, Permission, UsersGroupToPerm, User
from rhodecode.lib.exceptions import UsersGroupsAssignedException

log = logging.getLogger(__name__)


class UsersGroupModel(BaseModel):

    def __get_user(self, user):
        return self._get_instance(User, user, callback=User.get_by_username)

    def __get_users_group(self, users_group):
        return self._get_instance(UsersGroup, users_group,
                                  callback=UsersGroup.get_by_group_name)

    def __get_perm(self, permission):
        return self._get_instance(Permission, permission,
                                  callback=Permission.get_by_key)

    def get(self, users_group_id, cache=False):
        return UsersGroup.get(users_group_id)

    def get_by_name(self, name, cache=False, case_insensitive=False):
        return UsersGroup.get_by_group_name(name, cache, case_insensitive)

    def create(self, name, active=True):
        try:
            new = UsersGroup()
            new.users_group_name = name
            new.users_group_active = active
            self.sa.add(new)
            return new
        except:
            log.error(traceback.format_exc())
            raise

    def update(self, users_group, form_data):

        try:
            users_group = self.__get_users_group(users_group)

            for k, v in form_data.items():
                if k == 'users_group_members':
                    users_group.members = []
                    self.sa.flush()
                    members_list = []
                    if v:
                        v = [v] if isinstance(v, basestring) else v
                        for u_id in set(v):
                            member = UsersGroupMember(users_group.users_group_id, u_id)
                            members_list.append(member)
                    setattr(users_group, 'members', members_list)
                setattr(users_group, k, v)

            self.sa.add(users_group)
        except:
            log.error(traceback.format_exc())
            raise

    def delete(self, users_group, force=False):
        """
        Deletes repos group, unless force flag is used
        raises exception if there are members in that group, else deletes
        group and users

        :param users_group:
        :param force:
        """
        try:
            users_group = self.__get_users_group(users_group)

            # check if this group is not assigned to repo
            assigned_groups = UsersGroupRepoToPerm.query()\
                .filter(UsersGroupRepoToPerm.users_group == users_group).all()

            if assigned_groups and force is False:
                raise UsersGroupsAssignedException('RepoGroup assigned to %s' %
                                                   assigned_groups)

            self.sa.delete(users_group)
        except:
            log.error(traceback.format_exc())
            raise

    def add_user_to_group(self, users_group, user):
        users_group = self.__get_users_group(users_group)
        user = self.__get_user(user)

        for m in users_group.members:
            u = m.user
            if u.user_id == user.user_id:
                return True

        try:
            users_group_member = UsersGroupMember()
            users_group_member.user = user
            users_group_member.users_group = users_group

            users_group.members.append(users_group_member)
            user.group_member.append(users_group_member)

            self.sa.add(users_group_member)
            return users_group_member
        except:
            log.error(traceback.format_exc())
            raise

    def remove_user_from_group(self, users_group, user):
        users_group = self.__get_users_group(users_group)
        user = self.__get_user(user)

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
            except:
                log.error(traceback.format_exc())
                raise
        else:
            # User isn't in that group
            return False

    def has_perm(self, users_group, perm):
        users_group = self.__get_users_group(users_group)
        perm = self.__get_perm(perm)

        return UsersGroupToPerm.query()\
            .filter(UsersGroupToPerm.users_group == users_group)\
            .filter(UsersGroupToPerm.permission == perm).scalar() is not None

    def grant_perm(self, users_group, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        users_group = self.__get_users_group(users_group)

        new = UsersGroupToPerm()
        new.users_group = users_group
        new.permission = perm
        self.sa.add(new)

    def revoke_perm(self, users_group, perm):
        users_group = self.__get_users_group(users_group)
        perm = self.__get_perm(perm)

        obj = UsersGroupToPerm.query()\
            .filter(UsersGroupToPerm.users_group == users_group)\
            .filter(UsersGroupToPerm.permission == perm).scalar()
        if obj:
            self.sa.delete(obj)
