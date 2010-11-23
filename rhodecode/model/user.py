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
from rhodecode.lib.exceptions import *
import logging
import traceback

log = logging.getLogger(__name__)



class UserModel(object):

    def __init__(self):
        self.sa = Session()

    def get(self, user_id, cache=False):
        user = self.sa.query(User)
        if cache:
            user = user.options(FromCache("sql_cache_short",
                                          "get_user_%s" % user_id))
        return user.get(user_id)


    def get_by_username(self, username, cache=False, case_insensitive=False):
        
        if case_insensitive:
            user = self.sa.query(User).filter(User.username.ilike(username))
        else:
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

    def create_ldap(self, username, password):
        """
        Checks if user is in database, if not creates this user marked
        as ldap user
        :param username:
        :param password:
        """

        if self.get_by_username(username) is None:
            try:
                new_user = User()
                new_user.username = username
                new_user.password = password
                new_user.email = '%s@ldap.server' % username
                new_user.active = True
                new_user.is_ldap = True
                new_user.name = '%s@ldap' % username
                new_user.lastname = ''


                self.sa.add(new_user)
                self.sa.commit()
                return True
            except:
                log.error(traceback.format_exc())
                self.sa.rollback()
                raise

        return False

    def create_registration(self, form_data):
        from rhodecode.lib.celerylib import tasks, run_task
        try:
            new_user = User()
            for k, v in form_data.items():
                if k != 'admin':
                    setattr(new_user, k, v)

            self.sa.add(new_user)
            self.sa.commit()
            body = ('New user registration\n'
                    'username: %s\n'
                    'email: %s\n')
            body = body % (form_data['username'], form_data['email'])

            run_task(tasks.send_email, None,
                     _('[RhodeCode] New User registration'),
                     body)
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
            if user.repositories:
                raise UserOwnsReposException(_('This user still owns %s '
                                               'repositories and cannot be '
                                               'removed. Switch owners or '
                                               'remove those repositories') \
                                               % user.repositories)
            self.sa.delete(user)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def reset_password(self, data):
        from rhodecode.lib.celerylib import tasks, run_task
        run_task(tasks.reset_user_password, data['email'])


    def fill_data(self, user):
        """
        Fills user data with those from database and log out user if not 
        present in database
        :param user:
        """

        if not hasattr(user, 'user_id') or user.user_id is None:
            raise Exception('passed in user has to have the user_id attribute')


        log.debug('filling auth user data')
        try:
            dbuser = self.get(user.user_id)
            user.username = dbuser.username
            user.is_admin = dbuser.admin
            user.name = dbuser.name
            user.lastname = dbuser.lastname
            user.email = dbuser.email
        except:
            log.error(traceback.format_exc())
            user.is_authenticated = False

        return user
