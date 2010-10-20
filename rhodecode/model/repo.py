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
:author: marcink
"""

from datetime import datetime
from pylons import app_globals as g
from rhodecode.model.db import Repository, RepoToPerm, User, Permission
from rhodecode.model.meta import Session
from rhodecode.model.user import UserModel
from rhodecode.model.caching_query import FromCache
import logging
import os
import shutil
import traceback
log = logging.getLogger(__name__)

class RepoModel(object):

    def __init__(self, sa=None):
        if not sa:
            self.sa = Session()
        else:
            self.sa = sa

    def get(self, repo_id, cache=False):
        repo = self.sa.query(Repository)\
            .filter(Repository.repo_name == repo_id)

        if cache:
            repo = repo.options(FromCache("sql_cache_short",
                                          "get_repo_%s" % repo))
        return repo.scalar()

    def get_users_js(self):

        users = self.sa.query(User).filter(User.active == True).all()
        u_tmpl = '''{id:%s, fname:"%s", lname:"%s", nname:"%s"},'''
        users_array = '[%s];' % '\n'.join([u_tmpl % (u.user_id, u.name,
                                                    u.lastname, u.username)
                                        for u in users])
        return users_array


    def update(self, repo_name, form_data):
        try:

            #update permissions
            for username, perm in form_data['perms_updates']:
                r2p = self.sa.query(RepoToPerm)\
                        .filter(RepoToPerm.user == UserModel(self.sa).get_by_username(username, cache=False))\
                        .filter(RepoToPerm.repository == self.get(repo_name))\
                        .one()

                r2p.permission_id = self.sa.query(Permission).filter(
                                                Permission.permission_name ==
                                                perm).one().permission_id
                self.sa.add(r2p)

            #set new permissions
            for username, perm in form_data['perms_new']:
                r2p = RepoToPerm()
                r2p.repository = self.get(repo_name)
                r2p.user = UserModel(self.sa).get_by_username(username, cache=False)

                r2p.permission_id = self.sa.query(Permission).filter(
                                        Permission.permission_name == perm)\
                                        .one().permission_id
                self.sa.add(r2p)

            #update current repo
            cur_repo = self.get(repo_name, cache=False)

            for k, v in form_data.items():
                if k == 'user':
                    cur_repo.user_id = v
                else:
                    setattr(cur_repo, k, v)

            self.sa.add(cur_repo)

            if repo_name != form_data['repo_name']:
                #rename our data
                self.__rename_repo(repo_name, form_data['repo_name'])

            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def create(self, form_data, cur_user, just_db=False, fork=False):
        try:
            if fork:
                repo_name = str(form_data['fork_name'])
                org_name = str(form_data['repo_name'])

            else:
                org_name = repo_name = str(form_data['repo_name'])
            new_repo = Repository()
            for k, v in form_data.items():
                if k == 'repo_name':
                    v = repo_name
                setattr(new_repo, k, v)

            if fork:
                parent_repo = self.sa.query(Repository)\
                        .filter(Repository.repo_name == org_name).scalar()
                new_repo.fork = parent_repo

            new_repo.user_id = cur_user.user_id
            self.sa.add(new_repo)

            #create default permission
            repo_to_perm = RepoToPerm()
            default = 'repository.read'
            for p in UserModel(self.sa).get_by_username('default', cache=False).user_perms:
                if p.permission.permission_name.startswith('repository.'):
                    default = p.permission.permission_name
                    break

            default_perm = 'repository.none' if form_data['private'] else default

            repo_to_perm.permission_id = self.sa.query(Permission)\
                    .filter(Permission.permission_name == default_perm)\
                    .one().permission_id

            repo_to_perm.repository_id = new_repo.repo_id
            repo_to_perm.user_id = UserModel(self.sa).get_by_username('default', cache=False).user_id

            self.sa.add(repo_to_perm)
            self.sa.commit()
            if not just_db:
                self.__create_repo(repo_name)
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def create_fork(self, form_data, cur_user):
        from rhodecode.lib.celerylib import tasks, run_task
        run_task(tasks.create_repo_fork, form_data, cur_user)

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
            self.sa.query(RepoToPerm)\
                .filter(RepoToPerm.repository == self.get(repo_name))\
                .filter(RepoToPerm.user_id == form_data['user_id']).delete()
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def __create_repo(self, repo_name):
        from rhodecode.lib.utils import check_repo
        repo_path = os.path.join(g.base_path, repo_name)
        if check_repo(repo_name, g.base_path):
            log.info('creating repo %s in %s', repo_name, repo_path)
            from vcs.backends.hg import MercurialRepository
            MercurialRepository(repo_path, create=True)

    def __rename_repo(self, old, new):
        log.info('renaming repo from %s to %s', old, new)

        old_path = os.path.join(g.base_path, old)
        new_path = os.path.join(g.base_path, new)
        if os.path.isdir(new_path):
            raise Exception('Was trying to rename to already existing dir %s',
                            new_path)
        shutil.move(old_path, new_path)

    def __delete_repo(self, name):
        rm_path = os.path.join(g.base_path, name)
        log.info("Removing %s", rm_path)
        #disable hg 
        shutil.move(os.path.join(rm_path, '.hg'), os.path.join(rm_path, 'rm__.hg'))
        #disable repo
        shutil.move(rm_path, os.path.join(g.base_path, 'rm__%s__%s' \
                                          % (datetime.today(), name)))
