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

    def __create_group(self, group_name):
        """
        makes repositories group on filesystem

        :param repo_name:
        :param parent_id:
        """

        create_path = os.path.join(self.repos_path, group_name)
        log.debug('creating new group in %s', create_path)

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

        log.debug('renaming repos group from %s to %s', old, new)


        old_path = os.path.join(self.repos_path, old)
        new_path = os.path.join(self.repos_path, new)

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
        if os.path.isdir(rm_path):
            # delete only if that path really exists
            os.rmdir(rm_path)

    def create(self, form_data):
        try:
            new_repos_group = Group()
            new_repos_group.group_description = form_data['group_description']
            new_repos_group.parent_group = Group.get(form_data['group_parent_id'])
            new_repos_group.group_name = new_repos_group.get_new_name(form_data['group_name'])

            self.sa.add(new_repos_group)

            self.__create_group(new_repos_group.group_name)

            self.sa.commit()
            return new_repos_group
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def update(self, repos_group_id, form_data):

        try:
            repos_group = Group.get(repos_group_id)
            old_path = repos_group.full_path
                
            # change properties
            repos_group.group_description = form_data['group_description']
            repos_group.parent_group = Group.get(form_data['group_parent_id'])
            repos_group.group_name = repos_group.get_new_name(form_data['group_name'])

            new_path = repos_group.full_path

            self.sa.add(repos_group)

            self.__rename_group(old_path, new_path)

            # we need to get all repositories from this new group and 
            # rename them accordingly to new group path
            for r in repos_group.repositories:
                r.repo_name = r.get_new_name(r.just_name)
                self.sa.add(r)

            self.sa.commit()
            return repos_group
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
