# -*- coding: utf-8 -*-
"""
    rhodecode.model.repo
    ~~~~~~~~~~~~~~~~~~~~

    Repository model for rhodecode

    :created_on: Jun 5, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
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

from rhodecode.lib.vcs.backends import get_backend

from rhodecode.lib import LazyProperty
from rhodecode.lib import safe_str, safe_unicode
from rhodecode.lib.caching_query import FromCache
from rhodecode.lib.hooks import log_create_repository

from rhodecode.model import BaseModel
from rhodecode.model.db import Repository, UserRepoToPerm, User, Permission, \
    Statistics, UsersGroup, UsersGroupRepoToPerm, RhodeCodeUi, RepoGroup


log = logging.getLogger(__name__)


class RepoModel(BaseModel):

    def __get_user(self, user):
        return self._get_instance(User, user, callback=User.get_by_username)

    def __get_users_group(self, users_group):
        return self._get_instance(UsersGroup, users_group,
                                  callback=UsersGroup.get_by_group_name)

    def __get_repos_group(self, repos_group):
        return self._get_instance(RepoGroup, repos_group,
                                  callback=RepoGroup.get_by_group_name)

    def __get_repo(self, repository):
        return self._get_instance(Repository, repository,
                                  callback=Repository.get_by_repo_name)

    def __get_perm(self, permission):
        return self._get_instance(Permission, permission,
                                  callback=Permission.get_by_key)

    @LazyProperty
    def repos_path(self):
        """
        Get's the repositories root path from database
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

    def get_repo(self, repository):
        return self.__get_repo(repository)

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
                    # this updates existing one
                    RepoModel().grant_user_permission(
                        repo=cur_repo, user=member, perm=perm
                    )
                else:
                    RepoModel().grant_users_group_permission(
                        repo=cur_repo, group_name=member, perm=perm
                    )
            # set new permissions
            for member, perm, member_type in form_data['perms_new']:
                if member_type == 'user':
                    RepoModel().grant_user_permission(
                        repo=cur_repo, user=member, perm=perm
                    )
                else:
                    RepoModel().grant_users_group_permission(
                        repo=cur_repo, group_name=member, perm=perm
                    )

            # update current repo
            for k, v in form_data.items():
                if k == 'user':
                    cur_repo.user = User.get_by_username(v)
                elif k == 'repo_name':
                    pass
                elif k == 'repo_group':
                    cur_repo.group = RepoGroup.get(v)

                else:
                    setattr(cur_repo, k, v)

            new_name = cur_repo.get_new_name(form_data['repo_name'])
            cur_repo.repo_name = new_name

            self.sa.add(cur_repo)

            if repo_name != new_name:
                # rename repository
                self.__rename_repo(old=repo_name, new=new_name)

            return cur_repo
        except:
            log.error(traceback.format_exc())
            raise

    def create(self, form_data, cur_user, just_db=False, fork=False):
        from rhodecode.model.scm import ScmModel

        try:
            if fork:
                fork_parent_id = form_data['fork_parent_id']

            # repo name is just a name of repository
            # while repo_name_full is a full qualified name that is combined
            # with name and path of group
            repo_name = form_data['repo_name']
            repo_name_full = form_data['repo_name_full']

            new_repo = Repository()
            new_repo.enable_statistics = False

            for k, v in form_data.items():
                if k == 'repo_name':
                    v = repo_name_full
                if k == 'repo_group':
                    k = 'group_id'
                if k == 'description':
                    v = v or repo_name

                setattr(new_repo, k, v)

            if fork:
                parent_repo = Repository.get(fork_parent_id)
                new_repo.fork = parent_repo

            new_repo.user_id = cur_user.user_id
            self.sa.add(new_repo)

            def _create_default_perms():
                # create default permission
                repo_to_perm = UserRepoToPerm()
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

            if fork:
                if form_data.get('copy_permissions'):
                    repo = Repository.get(fork_parent_id)
                    user_perms = UserRepoToPerm.query()\
                        .filter(UserRepoToPerm.repository == repo).all()
                    group_perms = UsersGroupRepoToPerm.query()\
                        .filter(UsersGroupRepoToPerm.repository == repo).all()

                    for perm in user_perms:
                        UserRepoToPerm.create(perm.user, new_repo,
                                              perm.permission)

                    for perm in group_perms:
                        UsersGroupRepoToPerm.create(perm.users_group, new_repo,
                                                    perm.permission)
                else:
                    _create_default_perms()
            else:
                _create_default_perms()

            if not just_db:
                self.__create_repo(repo_name, form_data['repo_type'],
                                   form_data['repo_group'],
                                   form_data['clone_uri'])

            # now automatically start following this repository as owner
            ScmModel(self.sa).toggle_following_repo(new_repo.repo_id,
                                                    cur_user.user_id)
            log_create_repository(new_repo.get_dict(),
                                  created_by=cur_user.username)
            return new_repo
        except:
            log.error(traceback.format_exc())
            raise

    def create_fork(self, form_data, cur_user):
        """
        Simple wrapper into executing celery task for fork creation

        :param form_data:
        :param cur_user:
        """
        from rhodecode.lib.celerylib import tasks, run_task
        run_task(tasks.create_repo_fork, form_data, cur_user)

    def delete(self, repo):
        repo = self.__get_repo(repo)
        try:
            self.sa.delete(repo)
            self.__delete_repo(repo)
        except:
            log.error(traceback.format_exc())
            raise

    def grant_user_permission(self, repo, user, perm):
        """
        Grant permission for user on given repository, or update existing one
        if found

        :param repo: Instance of Repository, repository_id, or repository name
        :param user: Instance of User, user_id or username
        :param perm: Instance of Permission, or permission_name
        """
        user = self.__get_user(user)
        repo = self.__get_repo(repo)
        permission = self.__get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UserRepoToPerm)\
            .filter(UserRepoToPerm.user == user)\
            .filter(UserRepoToPerm.repository == repo)\
            .scalar()
        if obj is None:
            # create new !
            obj = UserRepoToPerm()
        obj.repository = repo
        obj.user = user
        obj.permission = permission
        self.sa.add(obj)

    def revoke_user_permission(self, repo, user):
        """
        Revoke permission for user on given repository

        :param repo: Instance of Repository, repository_id, or repository name
        :param user: Instance of User, user_id or username
        """
        user = self.__get_user(user)
        repo = self.__get_repo(repo)

        obj = self.sa.query(UserRepoToPerm)\
            .filter(UserRepoToPerm.repository == repo)\
            .filter(UserRepoToPerm.user == user)\
            .one()
        self.sa.delete(obj)

    def grant_users_group_permission(self, repo, group_name, perm):
        """
        Grant permission for users group on given repository, or update
        existing one if found

        :param repo: Instance of Repository, repository_id, or repository name
        :param group_name: Instance of UserGroup, users_group_id,
            or users group name
        :param perm: Instance of Permission, or permission_name
        """
        repo = self.__get_repo(repo)
        group_name = self.__get_users_group(group_name)
        permission = self.__get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UsersGroupRepoToPerm)\
            .filter(UsersGroupRepoToPerm.users_group == group_name)\
            .filter(UsersGroupRepoToPerm.repository == repo)\
            .scalar()

        if obj is None:
            # create new
            obj = UsersGroupRepoToPerm()

        obj.repository = repo
        obj.users_group = group_name
        obj.permission = permission
        self.sa.add(obj)

    def revoke_users_group_permission(self, repo, group_name):
        """
        Revoke permission for users group on given repository

        :param repo: Instance of Repository, repository_id, or repository name
        :param group_name: Instance of UserGroup, users_group_id,
            or users group name
        """
        repo = self.__get_repo(repo)
        group_name = self.__get_users_group(group_name)

        obj = self.sa.query(UsersGroupRepoToPerm)\
            .filter(UsersGroupRepoToPerm.repository == repo)\
            .filter(UsersGroupRepoToPerm.users_group == group_name)\
            .one()
        self.sa.delete(obj)

    def delete_stats(self, repo_name):
        """
        removes stats for given repo

        :param repo_name:
        """
        try:
            obj = self.sa.query(Statistics)\
                    .filter(Statistics.repository ==
                            self.get_by_repo_name(repo_name))\
                    .one()
            self.sa.delete(obj)
        except:
            log.error(traceback.format_exc())
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
            paths = RepoGroup.get(new_parent_id)\
                .full_path.split(RepoGroup.url_sep())
            new_parent_path = os.sep.join(paths)
        else:
            new_parent_path = ''

        # we need to make it str for mercurial
        repo_path = os.path.join(*map(lambda x: safe_str(x),
                                [self.repos_path, new_parent_path, repo_name]))

        # check if this path is not a repository
        if is_valid_repo(repo_path, self.repos_path):
            raise Exception('This path %s is a valid repository' % repo_path)

        # check if this path is a group
        if is_valid_repos_group(repo_path, self.repos_path):
            raise Exception('This path %s is a valid group' % repo_path)

        log.info('creating repo %s in %s @ %s' % (
                     repo_name, safe_unicode(repo_path), clone_uri
                )
        )
        backend = get_backend(alias)

        backend(repo_path, create=True, src_url=clone_uri)

    def __rename_repo(self, old, new):
        """
        renames repository on filesystem

        :param old: old name
        :param new: new name
        """
        log.info('renaming repo from %s to %s' % (old, new))

        old_path = os.path.join(self.repos_path, old)
        new_path = os.path.join(self.repos_path, new)
        if os.path.isdir(new_path):
            raise Exception(
                'Was trying to rename to already existing dir %s' % new_path
            )
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
        log.info("Removing %s" % (rm_path))
        # disable hg/git
        alias = repo.repo_type
        shutil.move(os.path.join(rm_path, '.%s' % alias),
                    os.path.join(rm_path, 'rm__.%s' % alias))
        # disable repo
        _d = 'rm__%s__%s' % (datetime.now().strftime('%Y%m%d_%H%M%S_%f'),
                             repo.repo_name)
        shutil.move(rm_path, os.path.join(self.repos_path, _d))
