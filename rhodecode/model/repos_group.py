# -*- coding: utf-8 -*-
"""
    rhodecode.model.user_group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    users groups model for RhodeCode

    :created_on: Jan 25, 2011
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
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

from pylons.i18n.translation import _

from vcs.utils.lazy import LazyProperty

from rhodecode.model import BaseModel
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import Group, RhodeCodeUi

log = logging.getLogger(__name__)


class ReposGroupModel(BaseModel):

    @LazyProperty
    def repos_path(self):
        """
        Get's the repositories root path from database
        """

        q = RhodeCodeUi.get_by_key('/').one()
        return q.ui_value

    def __create_group(self, group_name, parent_id):
        """
        makes repositories group on filesystem

        :param repo_name:
        :param parent_id:
        """

        if parent_id:
            paths = Group.get(parent_id).full_path.split(Group.url_sep())
            parent_path = os.sep.join(paths)
        else:
            parent_path = ''

        create_path = os.path.join(self.repos_path, parent_path, group_name)
        log.debug('creating new group in %s', create_path)

        if os.path.isdir(create_path):
            raise Exception('That directory already exists !')


        os.makedirs(create_path)


    def __rename_group(self, old, old_parent_id, new, new_parent_id):
        """
        Renames a group on filesystem

        :param group_name:
        """
        log.debug('renaming repos group from %s to %s', old, new)

        if new_parent_id:
            paths = Group.get(new_parent_id).full_path.split(Group.url_sep())
            new_parent_path = os.sep.join(paths)
        else:
            new_parent_path = ''

        if old_parent_id:
            paths = Group.get(old_parent_id).full_path.split(Group.url_sep())
            old_parent_path = os.sep.join(paths)
        else:
            old_parent_path = ''

        old_path = os.path.join(self.repos_path, old_parent_path, old)
        new_path = os.path.join(self.repos_path, new_parent_path, new)

        log.debug('renaming repos paths from %s to %s', old_path, new_path)

        if os.path.isdir(new_path):
            raise Exception('Was trying to rename to already '
                            'existing dir %s' % new_path)
        shutil.move(old_path, new_path)

    def __delete_group(self, group):
        """
        Deletes a group from a filesystem

        :param group: instance of group from database
        """
        paths = group.full_path.split(Group.url_sep())
        paths = os.sep.join(paths)

        rm_path = os.path.join(self.repos_path, paths)
        os.rmdir(rm_path)

    def create(self, form_data):
        try:
            new_repos_group = Group()
            new_repos_group.group_name = form_data['group_name']
            new_repos_group.group_description = \
                form_data['group_description']
            new_repos_group.group_parent_id = form_data['group_parent_id']

            self.sa.add(new_repos_group)

            self.__create_group(form_data['group_name'],
                                form_data['group_parent_id'])

            self.sa.commit()
            return new_repos_group
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def update(self, repos_group_id, form_data):

        try:
            repos_group = Group.get(repos_group_id)
            old_name = repos_group.group_name
            old_parent_id = repos_group.group_parent_id

            repos_group.group_name = form_data['group_name']
            repos_group.group_description = \
                form_data['group_description']
            repos_group.group_parent_id = form_data['group_parent_id']

            self.sa.add(repos_group)

            if old_name != form_data['group_name'] or (old_parent_id !=
                                                form_data['group_parent_id']):
                self.__rename_group(old = old_name, old_parent_id = old_parent_id,
                                    new = form_data['group_name'],
                                    new_parent_id = form_data['group_parent_id'])

            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def delete(self, users_group_id):
        try:
            users_group = Group.get(users_group_id)
            self.sa.delete(users_group)
            self.__delete_group(users_group)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
