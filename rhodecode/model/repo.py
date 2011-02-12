# -*- coding: utf-8 -*-
"""
    rhodecode.model.repo
    ~~~~~~~~~~~~~~~~~~~~

    Repository model for rhodecode
    
    :created_on: Jun 5, 2010
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
import os
import shutil
import logging
import traceback
from datetime import datetime

from sqlalchemy.orm import joinedload

from vcs.utils.lazy import LazyProperty
from vcs.backends import get_backend

from rhodecode.model import BaseModel
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import Repository, RepoToPerm, User, Permission, \
    Statistics, UsersGroup, UsersGroupToPerm, RhodeCodeUi
from rhodecode.model.user import UserModel
from rhodecode.model.users_group import UsersGroupMember, UsersGroupModel


log = logging.getLogger(__name__)

class RepoModel(BaseModel):

    @LazyProperty
    def repos_path(self):
        """Get's the repositories root path from database
        """

        q = self.sa.query(RhodeCodeUi).filter(RhodeCodeUi.ui_key == '/').one()
        return q.ui_value

    def get(self, repo_id, cache=False):
        repo = self.sa.query(Repository)\
            .filter(Repository.repo_id == repo_id)

        if cache:
            repo = repo.options(FromCache("sql_cache_short",
                                          "get_repo_%s" % repo_id))
        return repo.scalar()


    def get_by_repo_name(self, repo_name, cache=False):
        repo = self.sa.query(Repository)\
            .filter(Repository.repo_name == repo_name)

        if cache:
            repo = repo.options(FromCache("sql_cache_short",
                                          "get_repo_%s" % repo_name))
        return repo.scalar()


    def get_full(self, repo_name, cache=False, invalidate=False):
        repo = self.sa.query(Repository)\
            .options(joinedload(Repository.fork))\
            .options(joinedload(Repository.user))\
            .options(joinedload(Repository.followers))\
            .options(joinedload(Repository.repo_to_perm))\
            .options(joinedload(Repository.users_group_to_perm))\
            .filter(Repository.repo_name == repo_name)\

        if cache:
            repo = repo.options(FromCache("sql_cache_long",
                                          "get_repo_full_%s" % repo_name))
        if invalidate:
            repo.invalidate()

        return repo.scalar()


    def get_users_js(self):

        users = self.sa.query(User).filter(User.active == True).all()
        u_tmpl = '''{id:%s, fname:"%s", lname:"%s", nname:"%s"},'''
        users_array = '[%s]' % '\n'.join([u_tmpl % (u.user_id, u.name,
                                                    u.lastname, u.username)
                                        for u in users])
        return users_array


    def get_users_groups_js(self):
        users_groups = self.sa.query(UsersGroup)\
            .filter(UsersGroup.users_group_active == True).all()

        g_tmpl = '''{id:%s, grname:"%s",grmembers:"%s"},'''

        users_groups_array = '[%s]' % '\n'.join([g_tmpl % \
                                    (gr.users_group_id, gr.users_group_name,
                                     len(gr.members))
                                        for gr in users_groups])
        return users_groups_array

    def update(self, repo_name, form_data):
        try:
            cur_repo = self.get_by_repo_name(repo_name, cache=False)
            user_model = UserModel(self.sa)
            users_group_model = UsersGroupModel(self.sa)

            #update permissions
            for member, perm, member_type in form_data['perms_updates']:
                if member_type == 'user':
                    r2p = self.sa.query(RepoToPerm)\
                            .filter(RepoToPerm.user == user_model.get_by_username(member))\
                            .filter(RepoToPerm.repository == cur_repo)\
                            .one()

                    r2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.permission_name == perm)\
                                        .scalar()
                    self.sa.add(r2p)
                else:
                    g2p = self.sa.query(UsersGroupToPerm)\
                            .filter(UsersGroupToPerm.users_group == users_group_model.get_by_groupname(member))\
                            .filter(UsersGroupToPerm.repository == cur_repo)\
                            .one()

                    g2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.permission_name == perm)\
                                        .scalar()
                    self.sa.add(g2p)

            #set new permissions
            for member, perm, member_type in form_data['perms_new']:
                if member_type == 'user':
                    r2p = RepoToPerm()
                    r2p.repository = cur_repo
                    r2p.user = user_model.get_by_username(member)

                    r2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.permission_name == perm)\
                                        .scalar()
                    self.sa.add(r2p)
                else:
                    g2p = UsersGroupToPerm()
                    g2p.repository = cur_repo
                    g2p.users_group = users_group_model.get_by_groupname(member)

                    g2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.permission_name == perm)\
                                        .scalar()
                    self.sa.add(g2p)

            #update current repo
            for k, v in form_data.items():
                if k == 'user':
                    cur_repo.user = user_model.get(v)
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
                #force str since hg doesn't go with unicode
                repo_name = str(form_data['fork_name'])
                org_name = str(form_data['repo_name'])

            else:
                org_name = repo_name = str(form_data['repo_name'])
            new_repo = Repository()
            new_repo.enable_statistics = True
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

            repo_to_perm.repository = new_repo
            repo_to_perm.user_id = UserModel(self.sa)\
                .get_by_username('default', cache=False).user_id

            self.sa.add(repo_to_perm)

            if not just_db:
                self.__create_repo(repo_name, form_data['repo_type'])

            self.sa.commit()

            #now automatically start following this repository as owner
            from rhodecode.model.scm import ScmModel
            ScmModel(self.sa).toggle_following_repo(new_repo.repo_id,
                                             cur_user.user_id)

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
            self.__delete_repo(repo)
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def delete_perm_user(self, form_data, repo_name):
        try:
            self.sa.query(RepoToPerm)\
                .filter(RepoToPerm.repository \
                        == self.get_by_repo_name(repo_name))\
                .filter(RepoToPerm.user_id == form_data['user_id']).delete()
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def delete_perm_users_group(self, form_data, repo_name):
        try:
            self.sa.query(UsersGroupToPerm)\
                .filter(UsersGroupToPerm.repository \
                        == self.get_by_repo_name(repo_name))\
                .filter(UsersGroupToPerm.users_group_id \
                        == form_data['users_group_id']).delete()
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def delete_stats(self, repo_name):
        try:
            self.sa.query(Statistics)\
                .filter(Statistics.repository == \
                        self.get_by_repo_name(repo_name)).delete()
            self.sa.commit()
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise


    def __create_repo(self, repo_name, alias):
        """
        makes repository on filesystem
        :param repo_name:
        :param alias:
        """
        from rhodecode.lib.utils import check_repo
        repo_path = os.path.join(self.repos_path, repo_name)
        if check_repo(repo_name, self.repos_path):
            log.info('creating repo %s in %s', repo_name, repo_path)
            backend = get_backend(alias)
            backend(repo_path, create=True)

    def __rename_repo(self, old, new):
        """
        renames repository on filesystem
        :param old: old name
        :param new: new name
        """
        log.info('renaming repo from %s to %s', old, new)

        old_path = os.path.join(self.repos_path, old)
        new_path = os.path.join(self.repos_path, new)
        if os.path.isdir(new_path):
            raise Exception('Was trying to rename to already existing dir %s',
                            new_path)
        shutil.move(old_path, new_path)

    def __delete_repo(self, repo):
        """
        removes repo from filesystem, the removal is acctually made by
        added rm__ prefix into dir, and rename internat .hg/.git dirs so this
        repository is no longer valid for rhodecode, can be undeleted later on
        by reverting the renames on this repository
        :param repo: repo object
        """
        rm_path = os.path.join(self.repos_path, repo.repo_name)
        log.info("Removing %s", rm_path)
        #disable hg/git
        alias = repo.repo_type
        shutil.move(os.path.join(rm_path, '.%s' % alias),
                    os.path.join(rm_path, 'rm__.%s' % alias))
        #disable repo
        shutil.move(rm_path, os.path.join(self.repos_path, 'rm__%s__%s' \
                                          % (datetime.today().isoformat(),
                                             repo.repo_name)))
