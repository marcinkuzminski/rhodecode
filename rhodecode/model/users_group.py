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

import logging
import traceback

from pylons.i18n.translation import _

from rhodecode.lib.exceptions import UsersGroupsAssignedException
from rhodecode.model import BaseModel
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import UsersGroup, UsersGroupMember, \
    UsersGroupRepoToPerm

log = logging.getLogger(__name__)


class UsersGroupModel(BaseModel):

    def get(self, users_group_id, cache=False):
        users_group = self.sa.query(UsersGroup)
        if cache:
            users_group = users_group.options(FromCache("sql_cache_short",
                                    "get_users_group_%s" % users_group_id))
        return users_group.get(users_group_id)

    def create(self, form_data):
        try:
            new_users_group = UsersGroup()
            for k, v in form_data.items():
                setattr(new_users_group, k, v)

            self.sa.add(new_users_group)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def update(self, users_group_id, form_data):

        try:
            users_group = self.get(users_group_id, cache=False)

            for k, v in form_data.items():
                if k == 'users_group_members':
                    users_group.members = []
                    self.sa.flush()
                    members_list = []
                    if v:
                        for u_id in set(v):
                            members_list.append(UsersGroupMember(
                                                            users_group_id,
                                                            u_id))
                    setattr(users_group, 'members', members_list)
                setattr(users_group, k, v)

            self.sa.add(users_group)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def delete(self, users_group_id):
        try:

            # check if this group is not assigned to repo
            assigned_groups = UsersGroupRepoToPerm.query()\
                .filter(UsersGroupRepoToPerm.users_group_id ==
                        users_group_id).all()

            if assigned_groups:
                raise UsersGroupsAssignedException('Group assigned to %s' %
                                                   assigned_groups)

            users_group = self.get(users_group_id, cache=False)
            self.sa.delete(users_group)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
