# -*- coding: utf-8 -*-
"""
    rhodecode.model.user_group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    users groups model for RhodeCode

    :created_on: Jan 25, 2011
    :author: marcink
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
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

import os
import logging
import traceback
import shutil

from rhodecode.lib import LazyProperty

from rhodecode.model import BaseModel
from rhodecode.model.db import RepoGroup, RhodeCodeUi, UserRepoGroupToPerm, \
    User, Permission, UsersGroupRepoGroupToPerm, UsersGroup

log = logging.getLogger(__name__)


class ReposGroupModel(BaseModel):

    def __get_user(self, user):
        return self._get_instance(User, user, callback=User.get_by_username)

    def __get_users_group(self, users_group):
        return self._get_instance(UsersGroup, users_group,
                                  callback=UsersGroup.get_by_group_name)

    def __get_repos_group(self, repos_group):
        return self._get_instance(RepoGroup, repos_group,
                                  callback=RepoGroup.get_by_group_name)

    def __get_perm(self, permission):
        return self._get_instance(Permission, permission,
                                  callback=Permission.get_by_key)

    @LazyProperty
    def repos_path(self):
        """
        Get's the repositories root path from database
        """

        q = RhodeCodeUi.get_by_key('/').one()
        return q.ui_value

    def _create_default_perms(self, new_group):
        # create default permission
        repo_group_to_perm = UserRepoGroupToPerm()
        default_perm = 'group.read'
        for p in User.get_by_username('default').user_perms:
            if p.permission.permission_name.startswith('group.'):
                default_perm = p.permission.permission_name
                break

        repo_group_to_perm.permission_id = self.sa.query(Permission)\
                .filter(Permission.permission_name == default_perm)\
                .one().permission_id

        repo_group_to_perm.group = new_group
        repo_group_to_perm.user_id = User.get_by_username('default').user_id

        self.sa.add(repo_group_to_perm)

    def __create_group(self, group_name):
        """
        makes repositories group on filesystem

        :param repo_name:
        :param parent_id:
        """

        create_path = os.path.join(self.repos_path, group_name)
        log.debug('creating new group in %s' % create_path)

        if os.path.isdir(create_path):
            raise Exception('That directory already exists !')

        os.makedirs(create_path)

    def __rename_group(self, old, new):
        """
        Renames a group on filesystem

        :param group_name:
        """

        if old == new:
            log.debug('skipping group rename')
            return

        log.debug('renaming repos group from %s to %s' % (old, new))

        old_path = os.path.join(self.repos_path, old)
        new_path = os.path.join(self.repos_path, new)

        log.debug('renaming repos paths from %s to %s' % (old_path, new_path))

        if os.path.isdir(new_path):
            raise Exception('Was trying to rename to already '
                            'existing dir %s' % new_path)
        shutil.move(old_path, new_path)

    def __delete_group(self, group):
        """
        Deletes a group from a filesystem

        :param group: instance of group from database
        """
        paths = group.full_path.split(RepoGroup.url_sep())
        paths = os.sep.join(paths)

        rm_path = os.path.join(self.repos_path, paths)
        if os.path.isdir(rm_path):
            # delete only if that path really exists
            os.rmdir(rm_path)

    def create(self, group_name, group_description, parent, just_db=False):
        try:
            new_repos_group = RepoGroup()
            new_repos_group.group_description = group_description
            new_repos_group.parent_group = self.__get_repos_group(parent)
            new_repos_group.group_name = new_repos_group.get_new_name(group_name)

            self.sa.add(new_repos_group)
            self._create_default_perms(new_repos_group)

            if not just_db:
                # we need to flush here, in order to check if database won't
                # throw any exceptions, create filesystem dirs at the very end
                self.sa.flush()
                self.__create_group(new_repos_group.group_name)

            return new_repos_group
        except:
            log.error(traceback.format_exc())
            raise

    def update(self, repos_group_id, form_data):

        try:
            repos_group = RepoGroup.get(repos_group_id)

            # update permissions
            for member, perm, member_type in form_data['perms_updates']:
                if member_type == 'user':
                    # this updates also current one if found
                    ReposGroupModel().grant_user_permission(
                        repos_group=repos_group, user=member, perm=perm
                    )
                else:
                    ReposGroupModel().grant_users_group_permission(
                        repos_group=repos_group, group_name=member, perm=perm
                    )
            # set new permissions
            for member, perm, member_type in form_data['perms_new']:
                if member_type == 'user':
                    ReposGroupModel().grant_user_permission(
                        repos_group=repos_group, user=member, perm=perm
                    )
                else:
                    ReposGroupModel().grant_users_group_permission(
                        repos_group=repos_group, group_name=member, perm=perm
                    )

            old_path = repos_group.full_path

            # change properties
            repos_group.group_description = form_data['group_description']
            repos_group.parent_group = RepoGroup.get(form_data['group_parent_id'])
            repos_group.group_parent_id = form_data['group_parent_id']
            repos_group.group_name = repos_group.get_new_name(form_data['group_name'])
            new_path = repos_group.full_path

            self.sa.add(repos_group)

            # we need to get all repositories from this new group and
            # rename them accordingly to new group path
            for r in repos_group.repositories:
                r.repo_name = r.get_new_name(r.just_name)
                self.sa.add(r)

            self.__rename_group(old_path, new_path)

            return repos_group
        except:
            log.error(traceback.format_exc())
            raise

    def delete(self, users_group_id):
        try:
            users_group = RepoGroup.get(users_group_id)
            self.sa.delete(users_group)
            self.__delete_group(users_group)
        except:
            log.error(traceback.format_exc())
            raise

    def grant_user_permission(self, repos_group, user, perm):
        """
        Grant permission for user on given repositories group, or update
        existing one if found

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param user: Instance of User, user_id or username
        :param perm: Instance of Permission, or permission_name
        """

        repos_group = self.__get_repos_group(repos_group)
        user = self.__get_user(user)
        permission = self.__get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UserRepoGroupToPerm)\
            .filter(UserRepoGroupToPerm.user == user)\
            .filter(UserRepoGroupToPerm.group == repos_group)\
            .scalar()
        if obj is None:
            # create new !
            obj = UserRepoGroupToPerm()
        obj.group = repos_group
        obj.user = user
        obj.permission = permission
        self.sa.add(obj)

    def revoke_user_permission(self, repos_group, user):
        """
        Revoke permission for user on given repositories group

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param user: Instance of User, user_id or username
        """

        repos_group = self.__get_repos_group(repos_group)
        user = self.__get_user(user)

        obj = self.sa.query(UserRepoGroupToPerm)\
            .filter(UserRepoGroupToPerm.user == user)\
            .filter(UserRepoGroupToPerm.group == repos_group)\
            .one()
        self.sa.delete(obj)

    def grant_users_group_permission(self, repos_group, group_name, perm):
        """
        Grant permission for users group on given repositories group, or update
        existing one if found

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param group_name: Instance of UserGroup, users_group_id,
            or users group name
        :param perm: Instance of Permission, or permission_name
        """
        repos_group = self.__get_repos_group(repos_group)
        group_name = self.__get_users_group(group_name)
        permission = self.__get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UsersGroupRepoGroupToPerm)\
            .filter(UsersGroupRepoGroupToPerm.group == repos_group)\
            .filter(UsersGroupRepoGroupToPerm.users_group == group_name)\
            .scalar()

        if obj is None:
            # create new
            obj = UsersGroupRepoGroupToPerm()

        obj.group = repos_group
        obj.users_group = group_name
        obj.permission = permission
        self.sa.add(obj)

    def revoke_users_group_permission(self, repos_group, group_name):
        """
        Revoke permission for users group on given repositories group

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param group_name: Instance of UserGroup, users_group_id,
            or users group name
        """
        repos_group = self.__get_repos_group(repos_group)
        group_name = self.__get_users_group(group_name)

        obj = self.sa.query(UsersGroupRepoGroupToPerm)\
            .filter(UsersGroupRepoGroupToPerm.group == repos_group)\
            .filter(UsersGroupRepoGroupToPerm.users_group == group_name)\
            .one()
        self.sa.delete(obj)
