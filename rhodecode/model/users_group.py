# -*- coding: utf-8 -*-
"""
    rhodecode.model.users_group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    users group model for RhodeCode

    :created_on: Oct 1, 2011
    :author: nvinot
    :copyright: (C) 2011-2011 Nicolas Vinot <aeris@imirhil.fr>
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
from rhodecode.model.db import UsersGroupMember, UsersGroup

log = logging.getLogger(__name__)


class UsersGroupModel(BaseModel):

    def __get_users_group(self, users_group):
        return self._get_instance(UsersGroup, users_group)

    def get(self, users_group_id, cache=False):
        return UsersGroup.get(users_group_id)

    def get_by_name(self, name, cache=False, case_insensitive=False):
        return UsersGroup.get_by_group_name(name, cache, case_insensitive)

    def create(self, form_data):
        try:
            new_users_group = UsersGroup()
            for k, v in form_data.items():
                setattr(new_users_group, k, v)

            self.sa.add(new_users_group)
            self.sa.commit()
            return new_users_group
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise


    def create_(self, name, active=True):
        new = UsersGroup()
        new.users_group_name = name
        new.users_group_active = active
        self.sa.add(new)
        return new

    def delete(self, users_group):
        obj = self.__get_users_group(users_group)
        self.sa.delete(obj)

    def add_user_to_group(self, users_group, user):
        for m in users_group.members:
            u = m.user
            if u.user_id == user.user_id:
                return m

        try:
            users_group_member = UsersGroupMember()
            users_group_member.user = user
            users_group_member.users_group = users_group

            users_group.members.append(users_group_member)
            user.group_member.append(users_group_member)

            self.sa.add(users_group_member)
            self.sa.commit()
            return users_group_member
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
