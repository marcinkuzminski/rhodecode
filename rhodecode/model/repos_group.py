# -*- coding: utf-8 -*-
"""
    rhodecode.model.user_group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    repo group model for RhodeCode

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
import datetime

from rhodecode.lib.utils2 import LazyProperty

from rhodecode.model import BaseModel
from rhodecode.model.db import RepoGroup, RhodeCodeUi, UserRepoGroupToPerm, \
    User, Permission, UserGroupRepoGroupToPerm, UserGroup, Repository

log = logging.getLogger(__name__)


class ReposGroupModel(BaseModel):

    cls = RepoGroup

    def _get_user_group(self, users_group):
        return self._get_instance(UserGroup, users_group,
                                  callback=UserGroup.get_by_group_name)

    def _get_repo_group(self, repos_group):
        return self._get_instance(RepoGroup, repos_group,
                                  callback=RepoGroup.get_by_group_name)

    @LazyProperty
    def repos_path(self):
        """
        Get's the repositories root path from database
        """

        q = RhodeCodeUi.get_by_key('/')
        return q.ui_value

    def _create_default_perms(self, new_group):
        # create default permission
        default_perm = 'group.read'
        def_user = User.get_default_user()
        for p in def_user.user_perms:
            if p.permission.permission_name.startswith('group.'):
                default_perm = p.permission.permission_name
                break

        repo_group_to_perm = UserRepoGroupToPerm()
        repo_group_to_perm.permission = Permission.get_by_key(default_perm)

        repo_group_to_perm.group = new_group
        repo_group_to_perm.user_id = def_user.user_id
        return repo_group_to_perm

    def __create_group(self, group_name):
        """
        makes repository group on filesystem

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

        log.debug('renaming repository group from %s to %s' % (old, new))

        old_path = os.path.join(self.repos_path, old)
        new_path = os.path.join(self.repos_path, new)

        log.debug('renaming repos paths from %s to %s' % (old_path, new_path))

        if os.path.isdir(new_path):
            raise Exception('Was trying to rename to already '
                            'existing dir %s' % new_path)
        shutil.move(old_path, new_path)

    def __delete_group(self, group, force_delete=False):
        """
        Deletes a group from a filesystem

        :param group: instance of group from database
        :param force_delete: use shutil rmtree to remove all objects
        """
        paths = group.full_path.split(RepoGroup.url_sep())
        paths = os.sep.join(paths)

        rm_path = os.path.join(self.repos_path, paths)
        log.info("Removing group %s" % (rm_path))
        # delete only if that path really exists
        if os.path.isdir(rm_path):
            if force_delete:
                shutil.rmtree(rm_path)
            else:
                #archive that group`
                _now = datetime.datetime.now()
                _ms = str(_now.microsecond).rjust(6, '0')
                _d = 'rm__%s_GROUP_%s' % (_now.strftime('%Y%m%d_%H%M%S_' + _ms),
                                          group.name)
                shutil.move(rm_path, os.path.join(self.repos_path, _d))

    def create(self, group_name, group_description, owner, parent=None, just_db=False):
        try:
            new_repos_group = RepoGroup()
            new_repos_group.user = self._get_user(owner)
            new_repos_group.group_description = group_description or group_name
            new_repos_group.parent_group = self._get_repo_group(parent)
            new_repos_group.group_name = new_repos_group.get_new_name(group_name)

            self.sa.add(new_repos_group)
            perm_obj = self._create_default_perms(new_repos_group)
            self.sa.add(perm_obj)

            #create an ADMIN permission for owner, later owner should go into
            #the owner field of groups
            self.grant_user_permission(repos_group=new_repos_group,
                                       user=owner, perm='group.admin')

            if not just_db:
                # we need to flush here, in order to check if database won't
                # throw any exceptions, create filesystem dirs at the very end
                self.sa.flush()
                self.__create_group(new_repos_group.group_name)

            return new_repos_group
        except Exception:
            log.error(traceback.format_exc())
            raise

    def _update_permissions(self, repos_group, perms_new=None,
                            perms_updates=None, recursive=False):
        from rhodecode.model.repo import RepoModel
        from rhodecode.lib.auth import HasUserGroupPermissionAny
        if not perms_new:
            perms_new = []
        if not perms_updates:
            perms_updates = []

        def _set_perm_user(obj, user, perm):
            if isinstance(obj, RepoGroup):
                self.grant_user_permission(
                    repos_group=obj, user=user, perm=perm
                )
            elif isinstance(obj, Repository):
                #we do this ONLY IF repository is non-private
                if obj.private:
                    return

                # we set group permission but we have to switch to repo
                # permission
                perm = perm.replace('group.', 'repository.')
                RepoModel().grant_user_permission(
                    repo=obj, user=user, perm=perm
                )

        def _set_perm_group(obj, users_group, perm):
            if isinstance(obj, RepoGroup):
                self.grant_users_group_permission(
                    repos_group=obj, group_name=users_group, perm=perm
                )
            elif isinstance(obj, Repository):
                # we set group permission but we have to switch to repo
                # permission
                perm = perm.replace('group.', 'repository.')
                RepoModel().grant_users_group_permission(
                    repo=obj, group_name=users_group, perm=perm
                )
        updates = []
        log.debug('Now updating permissions for %s in recursive mode:%s'
                  % (repos_group, recursive))

        for obj in repos_group.recursive_groups_and_repos():
            #obj is an instance of a group or repositories in that group
            if not recursive:
                obj = repos_group

            # update permissions
            for member, perm, member_type in perms_updates:
                ## set for user
                if member_type == 'user':
                    # this updates also current one if found
                    _set_perm_user(obj, user=member, perm=perm)
                ## set for user group
                else:
                    #check if we have permissions to alter this usergroup
                    if HasUserGroupPermissionAny('usergroup.read', 'usergroup.write',
                                                 'usergroup.admin')(member):
                        _set_perm_group(obj, users_group=member, perm=perm)
            # set new permissions
            for member, perm, member_type in perms_new:
                if member_type == 'user':
                    _set_perm_user(obj, user=member, perm=perm)
                else:
                    #check if we have permissions to alter this usergroup
                    if HasUserGroupPermissionAny('usergroup.read', 'usergroup.write',
                                                 'usergroup.admin')(member):
                        _set_perm_group(obj, users_group=member, perm=perm)
            updates.append(obj)
            #if it's not recursive call
            # break the loop and don't proceed with other changes
            if not recursive:
                break
        return updates

    def update(self, repos_group, form_data):

        try:
            repos_group = self._get_repo_group(repos_group)
            old_path = repos_group.full_path

            # change properties
            repos_group.group_description = form_data['group_description']
            repos_group.group_parent_id = form_data['group_parent_id']
            repos_group.enable_locking = form_data['enable_locking']

            repos_group.parent_group = RepoGroup.get(form_data['group_parent_id'])
            repos_group.group_name = repos_group.get_new_name(form_data['group_name'])
            new_path = repos_group.full_path
            self.sa.add(repos_group)

            # iterate over all members of this groups and do fixes
            # set locking if given
            # if obj is a repoGroup also fix the name of the group according
            # to the parent
            # if obj is a Repo fix it's name
            # this can be potentially heavy operation
            for obj in repos_group.recursive_groups_and_repos():
                #set the value from it's parent
                obj.enable_locking = repos_group.enable_locking
                if isinstance(obj, RepoGroup):
                    new_name = obj.get_new_name(obj.name)
                    log.debug('Fixing group %s to new name %s' \
                                % (obj.group_name, new_name))
                    obj.group_name = new_name
                elif isinstance(obj, Repository):
                    # we need to get all repositories from this new group and
                    # rename them accordingly to new group path
                    new_name = obj.get_new_name(obj.just_name)
                    log.debug('Fixing repo %s to new name %s' \
                                % (obj.repo_name, new_name))
                    obj.repo_name = new_name
                self.sa.add(obj)

            self.__rename_group(old_path, new_path)

            return repos_group
        except Exception:
            log.error(traceback.format_exc())
            raise

    def delete(self, repos_group, force_delete=False):
        repos_group = self._get_repo_group(repos_group)
        try:
            self.sa.delete(repos_group)
            self.__delete_group(repos_group, force_delete)
        except Exception:
            log.error('Error removing repos_group %s' % repos_group)
            raise

    def delete_permission(self, repos_group, obj, obj_type, recursive):
        """
        Revokes permission for repos_group for given obj(user or users_group),
        obj_type can be user or user group

        :param repos_group:
        :param obj: user or user group id
        :param obj_type: user or user group type
        :param recursive: recurse to all children of group
        """
        from rhodecode.model.repo import RepoModel
        repos_group = self._get_repo_group(repos_group)

        for el in repos_group.recursive_groups_and_repos():
            if not recursive:
                # if we don't recurse set the permission on only the top level
                # object
                el = repos_group

            if isinstance(el, RepoGroup):
                if obj_type == 'user':
                    ReposGroupModel().revoke_user_permission(el, user=obj)
                elif obj_type == 'users_group':
                    ReposGroupModel().revoke_users_group_permission(el, group_name=obj)
                else:
                    raise Exception('undefined object type %s' % obj_type)
            elif isinstance(el, Repository):
                if obj_type == 'user':
                    RepoModel().revoke_user_permission(el, user=obj)
                elif obj_type == 'users_group':
                    RepoModel().revoke_users_group_permission(el, group_name=obj)
                else:
                    raise Exception('undefined object type %s' % obj_type)

            #if it's not recursive call
            # break the loop and don't proceed with other changes
            if not recursive:
                break

    def grant_user_permission(self, repos_group, user, perm):
        """
        Grant permission for user on given repository group, or update
        existing one if found

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param user: Instance of User, user_id or username
        :param perm: Instance of Permission, or permission_name
        """

        repos_group = self._get_repo_group(repos_group)
        user = self._get_user(user)
        permission = self._get_perm(perm)

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
        log.debug('Granted perm %s to %s on %s' % (perm, user, repos_group))

    def revoke_user_permission(self, repos_group, user):
        """
        Revoke permission for user on given repository group

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param user: Instance of User, user_id or username
        """

        repos_group = self._get_repo_group(repos_group)
        user = self._get_user(user)

        obj = self.sa.query(UserRepoGroupToPerm)\
            .filter(UserRepoGroupToPerm.user == user)\
            .filter(UserRepoGroupToPerm.group == repos_group)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm on %s on %s' % (repos_group, user))

    def grant_users_group_permission(self, repos_group, group_name, perm):
        """
        Grant permission for user group on given repository group, or update
        existing one if found

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param group_name: Instance of UserGroup, users_group_id,
            or user group name
        :param perm: Instance of Permission, or permission_name
        """
        repos_group = self._get_repo_group(repos_group)
        group_name = self._get_user_group(group_name)
        permission = self._get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UserGroupRepoGroupToPerm)\
            .filter(UserGroupRepoGroupToPerm.group == repos_group)\
            .filter(UserGroupRepoGroupToPerm.users_group == group_name)\
            .scalar()

        if obj is None:
            # create new
            obj = UserGroupRepoGroupToPerm()

        obj.group = repos_group
        obj.users_group = group_name
        obj.permission = permission
        self.sa.add(obj)
        log.debug('Granted perm %s to %s on %s' % (perm, group_name, repos_group))

    def revoke_users_group_permission(self, repos_group, group_name):
        """
        Revoke permission for user group on given repository group

        :param repos_group: Instance of ReposGroup, repositories_group_id,
            or repositories_group name
        :param group_name: Instance of UserGroup, users_group_id,
            or user group name
        """
        repos_group = self._get_repo_group(repos_group)
        group_name = self._get_user_group(group_name)

        obj = self.sa.query(UserGroupRepoGroupToPerm)\
            .filter(UserGroupRepoGroupToPerm.group == repos_group)\
            .filter(UserGroupRepoGroupToPerm.users_group == group_name)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm to %s on %s' % (repos_group, group_name))
