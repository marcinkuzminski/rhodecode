#!/usr/bin/env python
# encoding: utf-8
# database management for RhodeCode
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
Created on April 10, 2010
database management and creation for RhodeCode
@author: marcink
"""

from os.path import dirname as dn, join as jn
import os
import sys
import uuid

from rhodecode.lib.auth import get_crypt_password
from rhodecode.lib.utils import ask_ok
from rhodecode.model import init_model
from rhodecode.model.db import User, Permission, RhodeCodeUi, RhodeCodeSettings, \
    UserToPerm
from rhodecode.model import meta
from sqlalchemy.engine import create_engine
import logging

log = logging.getLogger(__name__)

class DbManage(object):
    def __init__(self, log_sql, dbname, root, tests=False):
        self.dbname = dbname
        self.tests = tests
        self.root = root
        dburi = 'sqlite:////%s' % jn(self.root, self.dbname)
        engine = create_engine(dburi, echo=log_sql)
        init_model(engine)
        self.sa = meta.Session()
        self.db_exists = False

    def check_for_db(self, override):
        db_path = jn(self.root, self.dbname)
        log.info('checking for existing db in %s', db_path)
        if os.path.isfile(db_path):
            self.db_exists = True
            if not override:
                raise Exception('database already exists')

    def create_tables(self, override=False):
        """
        Create a auth database
        """
        self.check_for_db(override)
        if self.db_exists:
            log.info("database exist and it's going to be destroyed")
            if self.tests:
                destroy = True
            else:
                destroy = ask_ok('Are you sure to destroy old database ? [y/n]')
            if not destroy:
                sys.exit()
            if self.db_exists and destroy:
                os.remove(jn(self.root, self.dbname))
        checkfirst = not override
        meta.Base.metadata.create_all(checkfirst=checkfirst)
        log.info('Created tables for %s', self.dbname)

    def admin_prompt(self, second=False):
        if not self.tests:
            import getpass


            def get_password():
                password = getpass.getpass('Specify admin password (min 6 chars):')
                confirm = getpass.getpass('Confirm password:')

                if password != confirm:
                    log.error('passwords mismatch')
                    return False
                if len(password) < 6:
                    log.error('password is to short use at least 6 characters')
                    return False

                return password

            username = raw_input('Specify admin username:')

            password = get_password()
            if not password:
                #second try
                password = get_password()
                if not password:
                    sys.exit()

            email = raw_input('Specify admin email:')
            self.create_user(username, password, email, True)
        else:
            log.info('creating admin and regular test users')
            self.create_user('test_admin', 'test12', 'test_admin@mail.com', True)
            self.create_user('test_regular', 'test12', 'test_regular@mail.com', False)
            self.create_user('test_regular2', 'test12', 'test_regular2@mail.com', False)



    def config_prompt(self, test_repo_path=''):
        log.info('Setting up repositories config')

        if not self.tests and not test_repo_path:
            path = raw_input('Specify valid full path to your repositories'
                        ' you can change this later in application settings:')
        else:
            path = test_repo_path

        if not os.path.isdir(path):
            log.error('You entered wrong path: %s', path)
            sys.exit()

        hooks1 = RhodeCodeUi()
        hooks1.ui_section = 'hooks'
        hooks1.ui_key = 'changegroup.update'
        hooks1.ui_value = 'hg update >&2'
        hooks1.ui_active = False

        hooks2 = RhodeCodeUi()
        hooks2.ui_section = 'hooks'
        hooks2.ui_key = 'changegroup.repo_size'
        hooks2.ui_value = 'python:rhodecode.lib.hooks.repo_size'

        hooks3 = RhodeCodeUi()
        hooks3.ui_section = 'hooks'
        hooks3.ui_key = 'pretxnchangegroup.push_logger'
        hooks3.ui_value = 'python:rhodecode.lib.hooks.log_push_action'

        hooks4 = RhodeCodeUi()
        hooks4.ui_section = 'hooks'
        hooks4.ui_key = 'preoutgoing.pull_logger'
        hooks4.ui_value = 'python:rhodecode.lib.hooks.log_pull_action'


        web1 = RhodeCodeUi()
        web1.ui_section = 'web'
        web1.ui_key = 'push_ssl'
        web1.ui_value = 'false'

        web2 = RhodeCodeUi()
        web2.ui_section = 'web'
        web2.ui_key = 'allow_archive'
        web2.ui_value = 'gz zip bz2'

        web3 = RhodeCodeUi()
        web3.ui_section = 'web'
        web3.ui_key = 'allow_push'
        web3.ui_value = '*'

        web4 = RhodeCodeUi()
        web4.ui_section = 'web'
        web4.ui_key = 'baseurl'
        web4.ui_value = '/'

        paths = RhodeCodeUi()
        paths.ui_section = 'paths'
        paths.ui_key = '/'
        paths.ui_value = path


        hgsettings1 = RhodeCodeSettings('realm', 'RhodeCode authentication')
        hgsettings2 = RhodeCodeSettings('title', 'RhodeCode')


        try:


            self.sa.add(hooks1)
            self.sa.add(hooks2)
            self.sa.add(hooks3)
            self.sa.add(hooks4)
            self.sa.add(web1)
            self.sa.add(web2)
            self.sa.add(web3)
            self.sa.add(web4)
            self.sa.add(paths)
            self.sa.add(hgsettings1)
            self.sa.add(hgsettings2)
            for k in ['ldap_active', 'ldap_host', 'ldap_port', 'ldap_ldaps',
                      'ldap_dn_user', 'ldap_dn_pass', 'ldap_base_dn']:

                setting = RhodeCodeSettings(k, '')
                self.sa.add(setting)

            self.sa.commit()
        except:
            self.sa.rollback()
            raise
        log.info('created ui config')

    def create_user(self, username, password, email='', admin=False):
        log.info('creating administrator user %s', username)
        new_user = User()
        new_user.username = username
        new_user.password = get_crypt_password(password)
        new_user.name = 'RhodeCode'
        new_user.lastname = 'Admin'
        new_user.email = email
        new_user.admin = admin
        new_user.active = True

        try:
            self.sa.add(new_user)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise

    def create_default_user(self):
        log.info('creating default user')
        #create default user for handling default permissions.
        def_user = User()
        def_user.username = 'default'
        def_user.password = get_crypt_password(str(uuid.uuid1())[:8])
        def_user.name = 'Anonymous'
        def_user.lastname = 'User'
        def_user.email = 'anonymous@rhodecode.org'
        def_user.admin = False
        def_user.active = False
        try:
            self.sa.add(def_user)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise

    def create_permissions(self):
        #module.(access|create|change|delete)_[name]
        #module.(read|write|owner)
        perms = [('repository.none', 'Repository no access'),
                 ('repository.read', 'Repository read access'),
                 ('repository.write', 'Repository write access'),
                 ('repository.admin', 'Repository admin access'),
                 ('hg.admin', 'Hg Administrator'),
                 ('hg.create.repository', 'Repository create'),
                 ('hg.create.none', 'Repository creation disabled'),
                 ('hg.register.none', 'Register disabled'),
                 ('hg.register.manual_activate', 'Register new user with rhodecode without manual activation'),
                 ('hg.register.auto_activate', 'Register new user with rhodecode without auto activation'),
                ]

        for p in perms:
            new_perm = Permission()
            new_perm.permission_name = p[0]
            new_perm.permission_longname = p[1]
            try:
                self.sa.add(new_perm)
                self.sa.commit()
            except:
                self.sa.rollback()
                raise

    def populate_default_permissions(self):
        log.info('creating default user permissions')

        default_user = self.sa.query(User)\
        .filter(User.username == 'default').scalar()

        reg_perm = UserToPerm()
        reg_perm.user = default_user
        reg_perm.permission = self.sa.query(Permission)\
        .filter(Permission.permission_name == 'hg.register.manual_activate')\
        .scalar()

        create_repo_perm = UserToPerm()
        create_repo_perm.user = default_user
        create_repo_perm.permission = self.sa.query(Permission)\
        .filter(Permission.permission_name == 'hg.create.repository')\
        .scalar()

        default_repo_perm = UserToPerm()
        default_repo_perm.user = default_user
        default_repo_perm.permission = self.sa.query(Permission)\
        .filter(Permission.permission_name == 'repository.read')\
        .scalar()

        try:
            self.sa.add(reg_perm)
            self.sa.add(create_repo_perm)
            self.sa.add(default_repo_perm)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise

