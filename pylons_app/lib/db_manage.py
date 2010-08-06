#!/usr/bin/env python
# encoding: utf-8
# database managment for hg app
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
database managment and creation for hg app
@author: marcink
"""

from os.path import dirname as dn, join as jn
import os
import sys
import uuid
ROOT = dn(dn(dn(os.path.realpath(__file__))))
sys.path.append(ROOT)

from pylons_app.lib.auth import get_crypt_password
from pylons_app.lib.utils import ask_ok
from pylons_app.model import init_model
from pylons_app.model.db import User, Permission, HgAppUi, HgAppSettings
from pylons_app.model import meta
from sqlalchemy.engine import create_engine
import logging

log = logging.getLogger(__name__)

class DbManage(object):
    def __init__(self, log_sql):
        self.dbname = 'hg_app.db'
        dburi = 'sqlite:////%s' % jn(ROOT, self.dbname)
        engine = create_engine(dburi, echo=log_sql) 
        init_model(engine)
        self.sa = meta.Session
        self.db_exists = False
    
    def check_for_db(self, override):
        log.info('checking for exisiting db')
        if os.path.isfile(jn(ROOT, self.dbname)):
            self.db_exists = True
            log.info('database exisist')
            if not override:
                raise Exception('database already exists')

    def create_tables(self, override=False):
        """
        Create a auth database
        """
        self.check_for_db(override)
        if override:
            log.info("database exisist and it's going to be destroyed")
            destroy = ask_ok('Are you sure to destroy old database ? [y/n]')
            if not destroy:
                sys.exit()
            if self.db_exists and destroy:
                os.remove(jn(ROOT, self.dbname))
        checkfirst = not override
        meta.Base.metadata.create_all(checkfirst=checkfirst)
        log.info('Created tables for %s', self.dbname)
    
    def admin_prompt(self):
        import getpass
        username = raw_input('Specify admin username:')
        password = getpass.getpass('Specify admin password:')
        self.create_user(username, password, True)
    
    def config_prompt(self):
        log.info('Setting up repositories config')
        
        path = raw_input('Specify valid full path to your repositories'
                        ' you can change this later in application settings:')
        
        if not os.path.isdir(path):
            log.error('You entered wrong path')
            sys.exit()
        
        hooks1 = HgAppUi()
        hooks1.ui_section = 'hooks'
        hooks1.ui_key = 'changegroup.update'
        hooks1.ui_value = 'hg update >&2'
        
        hooks2 = HgAppUi()
        hooks2.ui_section = 'hooks'
        hooks2.ui_key = 'changegroup.repo_size'
        hooks2.ui_value = 'python:pylons_app.lib.hooks.repo_size' 
                
        web1 = HgAppUi()
        web1.ui_section = 'web'
        web1.ui_key = 'push_ssl'
        web1.ui_value = 'false'
                
        web2 = HgAppUi()
        web2.ui_section = 'web'
        web2.ui_key = 'allow_archive'
        web2.ui_value = 'gz zip bz2'
                
        web3 = HgAppUi()
        web3.ui_section = 'web'
        web3.ui_key = 'allow_push'
        web3.ui_value = '*'
        
        web4 = HgAppUi()
        web4.ui_section = 'web'
        web4.ui_key = 'baseurl'
        web4.ui_value = '/'                        
        
        paths = HgAppUi()
        paths.ui_section = 'paths'
        paths.ui_key = '/'
        paths.ui_value = os.path.join(path, '*')
        
        
        hgsettings1 = HgAppSettings()
        
        hgsettings1.app_settings_name = 'realm'
        hgsettings1.app_settings_value = 'hg-app authentication'
        
        hgsettings2 = HgAppSettings()
        hgsettings2.app_settings_name = 'title'
        hgsettings2.app_settings_value = 'hg-app'      
        
        try:
            self.sa.add(hooks1)
            self.sa.add(hooks2)
            self.sa.add(web1)
            self.sa.add(web2)
            self.sa.add(web3)
            self.sa.add(web4)
            self.sa.add(paths)
            self.sa.add(hgsettings1)
            self.sa.add(hgsettings2)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise        
        log.info('created ui config')
                    
    def create_user(self, username, password, admin=False):
        
        log.info('creating default user')
        #create default user for handling default permissions.
        def_user = User()
        def_user.username = 'default'
        def_user.password = get_crypt_password(str(uuid.uuid1())[:8])
        def_user.name = 'default'
        def_user.lastname = 'default'
        def_user.email = 'default@default.com'
        def_user.admin = False
        def_user.active = False
        
        log.info('creating administrator user %s', username)
        new_user = User()
        new_user.username = username
        new_user.password = get_crypt_password(password)
        new_user.name = 'Hg'
        new_user.lastname = 'Admin'
        new_user.email = 'admin@localhost'
        new_user.admin = admin
        new_user.active = True
        
        try:
            self.sa.add(def_user)
            self.sa.add(new_user)
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
                 ('repository.create', 'Repository create'),
                 ('hg.admin', 'Hg Administrator'),
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
