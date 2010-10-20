#!/usr/bin/env python
# encoding: utf-8
# Model for users
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
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
"""
Created on April 9, 2010
Model for users
:author: marcink
"""

from pylons.i18n.translation import _
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import User
from rhodecode.model.meta import Session
import logging
import traceback

log = logging.getLogger(__name__)

class DefaultUserException(Exception):pass

class UserModel(object):

    def __init__(self, sa=None):
        if not sa:
            self.sa = Session()
        else:
            self.sa = sa

    def get(self, user_id, cache=False):
        user = self.sa.query(User)
        if cache:
            user = user.options(FromCache("sql_cache_short",
                                          "get_user_%s" % user_id))
        return user.get(user_id)


    def get_by_username(self, username, cache=False):
        user = self.sa.query(User)\
            .filter(User.username == username)
        if cache:
            user = user.options(FromCache("sql_cache_short",
                                          "get_user_%s" % username))
        return user.scalar()

    def create(self, form_data):
        try:
            new_user = User()
            for k, v in form_data.items():
                setattr(new_user, k, v)

            self.sa.add(new_user)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def create_registration(self, form_data):
        try:
            new_user = User()
            for k, v in form_data.items():
                if k != 'admin':
                    setattr(new_user, k, v)

            self.sa.add(new_user)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def update(self, user_id, form_data):
        try:
            new_user = self.get(user_id, cache=False)
            if new_user.username == 'default':
                raise DefaultUserException(
                                _("You can't Edit this user since it's"
                                  " crucial for entire application"))
            for k, v in form_data.items():
                if k == 'new_password' and v != '':
                    new_user.password = v
                else:
                    setattr(new_user, k, v)

            self.sa.add(new_user)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def update_my_account(self, user_id, form_data):
        try:
            new_user = self.get(user_id, cache=False)
            if new_user.username == 'default':
                raise DefaultUserException(
                                _("You can't Edit this user since it's"
                                  " crucial for entire application"))
            for k, v in form_data.items():
                if k == 'new_password' and v != '':
                    new_user.password = v
                else:
                    if k not in ['admin', 'active']:
                        setattr(new_user, k, v)

            self.sa.add(new_user)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def delete(self, user_id):
        try:
            user = self.get(user_id, cache=False)
            if user.username == 'default':
                raise DefaultUserException(
                                _("You can't remove this user since it's"
                                  " crucial for entire application"))
            self.sa.delete(user)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def reset_password(self, data):
        from rhodecode.lib.celerylib import tasks, run_task
        run_task(tasks.reset_user_password, data['email'])
