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
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

import logging
import traceback

from pylons.i18n.translation import _

from rhodecode.model import BaseModel
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import UsersGroup, UsersGroupMember

from sqlalchemy.exc import DatabaseError

log = logging.getLogger(__name__)


class UsersGroupModel(BaseModel):

    def get(self, users_group_id, cache=False):
        users_group = self.sa.query(UsersGroup)
        if cache:
            users_group = users_group.options(FromCache("sql_cache_short",
                                          "get_users_group_%s" % users_group_id))
        return users_group.get(users_group_id)


    def get_by_groupname(self, users_group_name, cache=False,
                         case_insensitive=False):

        if case_insensitive:
            user = self.sa.query(UsersGroup)\
            .filter(UsersGroup.users_group_name.ilike(users_group_name))
        else:
            user = self.sa.query(UsersGroup)\
                .filter(UsersGroup.users_group_name == users_group_name)
        if cache:
            user = user.options(FromCache("sql_cache_short",
                                          "get_user_%s" % users_group_name))
        return user.scalar()

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
                            members_list.append(UsersGroupMember(users_group_id,
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
            users_group = self.get(users_group_id, cache=False)
            self.sa.delete(users_group)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
