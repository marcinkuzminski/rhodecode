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
import os
import shutil
import logging
import traceback
from datetime import datetime

from vcs.utils.lazy import LazyProperty
from vcs.backends import get_backend

from rhodecode.lib import safe_str, safe_unicode

from rhodecode.model import BaseModel
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import Repository, RepoToPerm, User, Permission, \
    Statistics, UsersGroup, UsersGroupRepoToPerm, RhodeCodeUi, Group

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

    def _get_defaults(self, repo_name):
        """
        Get's information about repository, and returns a dict for 
        usage in forms
        
        :param repo_name:
        """

        repo_info = Repository.get_by_repo_name(repo_name)

        if repo_info is None:
            return None

        defaults = repo_info.get_dict()
        group, repo_name = repo_info.groups_and_repo
        defaults['repo_name'] = repo_name
        defaults['repo_group'] = getattr(group[-1] if group else None,
                                         'group_id', None)

        # fill owner
        if repo_info.user:
            defaults.update({'user': repo_info.user.username})
        else:
            replacement_user = User.query().filter(User.admin ==
                                                   True).first().username
            defaults.update({'user': replacement_user})

        # fill repository users
        for p in repo_info.repo_to_perm:
            defaults.update({'u_perm_%s' % p.user.username:
                             p.permission.permission_name})

        # fill repository groups
        for p in repo_info.users_group_to_perm:
            defaults.update({'g_perm_%s' % p.users_group.users_group_name:
                             p.permission.permission_name})

        return defaults


    def update(self, repo_name, form_data):
        try:
            cur_repo = self.get_by_repo_name(repo_name, cache=False)

            # update permissions
            for member, perm, member_type in form_data['perms_updates']:
                if member_type == 'user':
                    r2p = self.sa.query(RepoToPerm)\
                            .filter(RepoToPerm.user == User.get_by_username(member))\
                            .filter(RepoToPerm.repository == cur_repo)\
                            .one()

                    r2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.permission_name ==
                                                perm).scalar()
                    self.sa.add(r2p)
                else:
                    g2p = self.sa.query(UsersGroupRepoToPerm)\
                            .filter(UsersGroupRepoToPerm.users_group ==
                                    UsersGroup.get_by_group_name(member))\
                            .filter(UsersGroupRepoToPerm.repository ==
                                    cur_repo).one()

                    g2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.permission_name ==
                                                perm).scalar()
                    self.sa.add(g2p)

            # set new permissions
            for member, perm, member_type in form_data['perms_new']:
                if member_type == 'user':
                    r2p = RepoToPerm()
                    r2p.repository = cur_repo
                    r2p.user = User.get_by_username(member)

                    r2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.
                                                permission_name == perm)\
                                                .scalar()
                    self.sa.add(r2p)
                else:
                    g2p = UsersGroupRepoToPerm()
                    g2p.repository = cur_repo
                    g2p.users_group = UsersGroup.get_by_group_name(member)
                    g2p.permission = self.sa.query(Permission)\
                                        .filter(Permission.
                                                permission_name == perm)\
                                                .scalar()
                    self.sa.add(g2p)

            # update current repo
            for k, v in form_data.items():
                if k == 'user':
                    cur_repo.user = User.get_by_username(v)
                elif k == 'repo_name':
                    pass
                elif k == 'repo_group':
                    cur_repo.group = Group.get(v)

                else:
                    setattr(cur_repo, k, v)

            new_name = cur_repo.get_new_name(form_data['repo_name'])
            cur_repo.repo_name = new_name

            self.sa.add(cur_repo)

            if repo_name != new_name:
                # rename repository
                self.__rename_repo(old=repo_name, new=new_name)

            self.sa.commit()
            return cur_repo
        except:
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise

    def create(self, form_data, cur_user, just_db=False, fork=False):

        try:
            if fork:
                repo_name = form_data['fork_name']
                org_name = form_data['repo_name']
                org_full_name = org_name

            else:
                org_name = repo_name = form_data['repo_name']
                repo_name_full = form_data['repo_name_full']

            new_repo = Repository()
            new_repo.enable_statistics = False
            for k, v in form_data.items():
                if k == 'repo_name':
                    if fork:
                        v = repo_name
                    else:
                        v = repo_name_full
                if k == 'repo_group':
                    k = 'group_id'

                if k == 'description':
                    v = safe_unicode(v) or repo_name

                setattr(new_repo, k, v)

            if fork:
                parent_repo = self.sa.query(Repository)\
                        .filter(Repository.repo_name == org_full_name).one()
                new_repo.fork = parent_repo

            new_repo.user_id = cur_user.user_id
            self.sa.add(new_repo)

            #create default permission
            repo_to_perm = RepoToPerm()
            default = 'repository.read'
            for p in User.get_by_username('default').user_perms:
                if p.permission.permission_name.startswith('repository.'):
                    default = p.permission.permission_name
                    break

            default_perm = 'repository.none' if form_data['private'] else default

            repo_to_perm.permission_id = self.sa.query(Permission)\
                    .filter(Permission.permission_name == default_perm)\
                    .one().permission_id

            repo_to_perm.repository = new_repo
            repo_to_perm.user_id = User.get_by_username('default').user_id

            self.sa.add(repo_to_perm)

            if not just_db:
                self.__create_repo(repo_name, form_data['repo_type'],
                                   form_data['repo_group'],
                                   form_data['clone_uri'])

            self.sa.commit()

            #now automatically start following this repository as owner
            from rhodecode.model.scm import ScmModel
            ScmModel(self.sa).toggle_following_repo(new_repo.repo_id,
                                             cur_user.user_id)
            return new_repo
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
            self.sa.query(UsersGroupRepoToPerm)\
                .filter(UsersGroupRepoToPerm.repository \
                        == self.get_by_repo_name(repo_name))\
                .filter(UsersGroupRepoToPerm.users_group_id \
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

    def __create_repo(self, repo_name, alias, new_parent_id, clone_uri=False):
        """
        makes repository on filesystem. It's group aware means it'll create
        a repository within a group, and alter the paths accordingly of
        group location

        :param repo_name:
        :param alias:
        :param parent_id:
        :param clone_uri:
        """
        from rhodecode.lib.utils import is_valid_repo, is_valid_repos_group

        if new_parent_id:
            paths = Group.get(new_parent_id).full_path.split(Group.url_sep())
            new_parent_path = os.sep.join(paths)
        else:
            new_parent_path = ''

        repo_path = os.path.join(*map(lambda x:safe_str(x),
                                [self.repos_path, new_parent_path, repo_name]))


        # check if this path is not a repository
        if is_valid_repo(repo_path, self.repos_path):
            raise Exception('This path %s is a valid repository' % repo_path)

        # check if this path is a group
        if is_valid_repos_group(repo_path, self.repos_path):
            raise Exception('This path %s is a valid group' % repo_path)

        log.info('creating repo %s in %s @ %s', repo_name, repo_path,
                 clone_uri)
        backend = get_backend(alias)

        backend(repo_path, create=True, src_url=clone_uri)


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
            raise Exception('Was trying to rename to already existing dir %s' \
            		     % new_path)
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
                                          % (datetime.today()\
                                             .strftime('%Y%m%d_%H%M%S_%f'),
                                            repo.repo_name)))

