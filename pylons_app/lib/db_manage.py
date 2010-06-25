#!/usr/bin/env python
# encoding: utf-8
# database managment for hg app
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
 
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
ROOT = dn(dn(dn(os.path.realpath(__file__))))
sys.path.append(ROOT)

from pylons_app.lib.auth import get_crypt_password
from pylons_app.model import init_model
from pylons_app.model.db import User, Permission
from pylons_app.model.meta import Session, Base
from sqlalchemy.engine import create_engine
import logging

log = logging.getLogger('db manage')
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s.%(msecs)03d" 
                                    " %(levelname)-5.5s [%(name)s] %(message)s"))
log.addHandler(console_handler)

class DbManage(object):
    def __init__(self, log_sql):
        self.dbname = 'hg_app.db'
        dburi = 'sqlite:////%s' % jn(ROOT, self.dbname)
        engine = create_engine(dburi, echo=log_sql) 
        init_model(engine)
        self.sa = Session()
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
            if self.db_exists:
                os.remove(jn(ROOT, self.dbname))
        Base.metadata.create_all(checkfirst=override)
        log.info('Created tables for %s', self.dbname)
    
    def admin_prompt(self):
        import getpass
        username = raw_input('Specify admin username:')
        password = getpass.getpass('Specify admin password:')
        self.create_user(username, password, True)
        
    def create_user(self, username, password, admin=False):
        
        log.info('creating default user')
        #create default user for handling default permissions.
        def_user = User()
        def_user.username = 'default'
        def_user.password = 'default'
        def_user.name = 'default'
        def_user.lastname = 'default'
        def_user.email = 'default@default'
        def_user.admin = False
        def_user.active = False
        
        self.sa.add(def_user)
        
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
        
        
        
if __name__ == '__main__':
    dbmanage = DbManage(log_sql=True)
    dbmanage.create_tables(override=True)
    dbmanage.admin_prompt()
    dbmanage.create_permissions()  


