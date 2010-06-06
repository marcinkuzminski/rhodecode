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
from pylons_app.model.db import Repository
import shutil
import os
from datetime import datetime
from pylons_app.lib.utils import check_repo
from pylons import app_globals as g
import logging
log = logging.getLogger(__name__)

class RepoModel(object):
    
    def __init__(self):
        self.sa = Session()
    
    def get(self, id):
        return self.sa.query(Repository).get(id)
        
    
    def update(self, id, form_data):
        try:
            if id != form_data['repo_name']:
                self.__rename_repo(id, form_data['repo_name'])
            cur_repo = self.sa.query(Repository).get(id)
            for k, v in form_data.items():
                if k == 'user':
                    cur_repo.user_id = v
                else:
                    setattr(cur_repo, k, v)
                
            self.sa.add(cur_repo)
            self.sa.commit()
        except Exception as e:
            log.error(e)
            self.sa.rollback()
            raise    
    
    def create(self, form_data, cur_user):
        try:
            new_repo = Repository()
            for k, v in form_data.items():
                setattr(new_repo, k, v)
                
            new_repo.user_id = cur_user.user_id
            self.sa.add(new_repo)
            self.sa.commit()
            self.__create_repo(form_data['repo_name'])
        except Exception as e:
            log.error(e)
            self.sa.rollback()
            raise    
                     
    def delete(self, repo):
        try:
            self.sa.delete(repo)
            self.sa.commit()
            self.__delete_repo(repo.repo_name)
        except Exception as e:
            log.error(e)
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
        shutil.move(rm_path, os.path.join(g.base_path, 'rm__%s-%s' % (datetime.today(), id)))
