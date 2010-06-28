#!/usr/bin/env python
# encoding: utf-8
# model for handling repositories actions
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
Created on Jun 5, 2010
model for handling repositories actions
@author: marcink
"""
from pylons_app.model.meta import Session
from pylons_app.model.db import Repository, Repo2Perm, User, Permission
import shutil
import os
from datetime import datetime
from pylons_app.lib.utils import check_repo
from pylons import app_globals as g
import traceback
import logging
log = logging.getLogger(__name__)

class RepoModel(object):
    
    def __init__(self):
        self.sa = Session()
    
    def get(self, id):
        return self.sa.query(Repository).get(id)
        
    def get_users_js(self):
        
        users = self.sa.query(User).all()
        u_tmpl = '''{id:%s, fname:"%s", lname:"%s", nname:"%s"},'''
        users_array = '[%s];' % '\n'.join([u_tmpl % (u.user_id, u.name,
                                                    u.lastname, u.username) 
                                        for u in users])
        return users_array        
        
    
    def update(self, repo_id, form_data):
        try:
            if repo_id != form_data['repo_name']:
                self.__rename_repo(repo_id, form_data['repo_name'])
            cur_repo = self.sa.query(Repository).get(repo_id)
            for k, v in form_data.items():
                if k == 'user':
                    cur_repo.user_id = v
                else:
                    setattr(cur_repo, k, v)
            
            #update permissions
            for username, perm in form_data['perms_updates']:
                r2p = self.sa.query(Repo2Perm)\
                        .filter(Repo2Perm.user == self.sa.query(User)\
                                .filter(User.username == username).one())\
                        .filter(Repo2Perm.repository == repo_id).one()
                
                r2p.permission_id = self.sa.query(Permission).filter(
                                                Permission.permission_name == 
                                                perm).one().permission_id
                self.sa.add(r2p)
            
            for username, perm in form_data['perms_new']:
                r2p = Repo2Perm()
                r2p.repository = repo_id
                r2p.user = self.sa.query(User)\
                                .filter(User.username == username).one()
                
                r2p.permission_id = self.sa.query(Permission).filter(
                                                Permission.permission_name == 
                                                perm).one().permission_id
                self.sa.add(r2p)
                                    
            self.sa.add(cur_repo)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise    
    
    def create(self, form_data, cur_user, just_db=False):
        try:
            repo_name = form_data['repo_name']
            new_repo = Repository()
            for k, v in form_data.items():
                setattr(new_repo, k, v)
                
            new_repo.user_id = cur_user.user_id
            self.sa.add(new_repo)

            #create default permission
            repo2perm = Repo2Perm()
            default_perm = 'repository.none' if form_data['private'] \
                                                        else 'repository.read'
            repo2perm.permission_id = self.sa.query(Permission)\
                    .filter(Permission.permission_name == default_perm)\
                    .one().permission_id
                        
            repo2perm.repository = repo_name
            repo2perm.user_id = self.sa.query(User)\
                    .filter(User.username == 'default').one().user_id 
            
            self.sa.add(repo2perm)
            self.sa.commit()
            if not just_db:
                self.__create_repo(repo_name)
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise    
                     
    def delete(self, repo):
        try:
            self.sa.delete(repo)
            self.sa.commit()
            self.__delete_repo(repo.repo_name)
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
    def delete_perm_user(self, form_data, repo_name):
        try:
            r2p = self.sa.query(Repo2Perm).filter(Repo2Perm.repository == repo_name)\
            .filter(Repo2Perm.user_id == form_data['user_id']).delete()
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
           
    def __create_repo(self, repo_name):        
        repo_path = os.path.join(g.base_path, repo_name)
        if check_repo(repo_name, g.base_path):
            log.info('creating repo %s in %s', repo_name, repo_path)
            from vcs.backends.hg import MercurialRepository
            MercurialRepository(repo_path, create=True)

    def __rename_repo(self, old, new):
        log.info('renaming repoo from %s to %s', old, new)
        old_path = os.path.join(g.base_path, old)
        new_path = os.path.join(g.base_path, new)
        shutil.move(old_path, new_path)
    
    def __delete_repo(self, name):
        rm_path = os.path.join(g.base_path, name)
        log.info("Removing %s", rm_path)
        #disable hg 
        shutil.move(os.path.join(rm_path, '.hg'), os.path.join(rm_path, 'rm__.hg'))
        #disable repo
        shutil.move(rm_path, os.path.join(g.base_path, 'rm__%s__%s' \
                                          % (datetime.today(), name)))
