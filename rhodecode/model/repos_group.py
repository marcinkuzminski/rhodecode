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
            parent_group_name = Group.get(parent_id).group_name
        else:
            parent_group_name = ''

        create_path = os.path.join(self.repos_path, parent_group_name,
                                   group_name)
        log.debug('creating new group in %s', create_path)

        if os.path.isdir(create_path):
            raise Exception('That directory already exists !')


        os.makedirs(create_path)


    def __rename_group(self, group_name):
        """
        Renames a group on filesystem
        
        :param group_name:
        """
        pass

    def __delete_group(self, group_name):
        """
        Deletes a group from a filesystem
        
        :param group_name:
        """
        pass

    def create(self, form_data):
        try:
            new_repos_group = Group()
            new_repos_group.group_name = form_data['repos_group_name']
            new_repos_group.group_description = \
                form_data['repos_group_description']
            new_repos_group.group_parent_id = form_data['repos_group_parent']

            self.sa.add(new_repos_group)

            self.__create_group(form_data['repos_group_name'],
                                form_data['repos_group_parent'])

            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def update(self, repos_group_id, form_data):

        try:
            repos_group = Group.get(repos_group_id)



            self.sa.add(repos_group)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def delete(self, users_group_id):
        try:
            users_group = self.get(users_group_id, cache=False)
            self.sa.delete(users_group)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
