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
from __future__ import with_statement
import os
import shutil
import logging
import traceback
from datetime import datetime

from rhodecode.lib.vcs.backends import get_backend
from rhodecode.lib.compat import json
from rhodecode.lib.utils2 import LazyProperty, safe_str, safe_unicode,\
    remove_prefix, obfuscate_url_pw
from rhodecode.lib.caching_query import FromCache
from rhodecode.lib.hooks import log_create_repository, log_delete_repository

from rhodecode.model import BaseModel
from rhodecode.model.db import Repository, UserRepoToPerm, User, Permission, \
    Statistics, UserGroup, UserGroupRepoToPerm, RhodeCodeUi, RepoGroup,\
    RhodeCodeSetting, RepositoryField
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import HasRepoPermissionAny, HasUserGroupPermissionAny
from rhodecode.lib.exceptions import AttachedForksError
from rhodecode.model.scm import UserGroupList

log = logging.getLogger(__name__)


class RepoModel(BaseModel):

    cls = Repository
    URL_SEPARATOR = Repository.url_sep()

    def _get_user_group(self, users_group):
        return self._get_instance(UserGroup, users_group,
                                  callback=UserGroup.get_by_group_name)

    def _get_repo_group(self, repos_group):
        return self._get_instance(RepoGroup, repos_group,
                                  callback=RepoGroup.get_by_group_name)

    def _create_default_perms(self, repository, private):
        # create default permission
        default = 'repository.read'
        def_user = User.get_default_user()
        for p in def_user.user_perms:
            if p.permission.permission_name.startswith('repository.'):
                default = p.permission.permission_name
                break

        default_perm = 'repository.none' if private else default

        repo_to_perm = UserRepoToPerm()
        repo_to_perm.permission = Permission.get_by_key(default_perm)

        repo_to_perm.repository = repository
        repo_to_perm.user_id = def_user.user_id

        return repo_to_perm

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
        return self._get_repo(repository)

    def get_by_repo_name(self, repo_name, cache=False):
        repo = self.sa.query(Repository)\
            .filter(Repository.repo_name == repo_name)

        if cache:
            repo = repo.options(FromCache("sql_cache_short",
                                          "get_repo_%s" % repo_name))
        return repo.scalar()

    def get_all_user_repos(self, user):
        """
        Get's all repositories that user have at least read access

        :param user:
        """
        from rhodecode.lib.auth import AuthUser
        user = self._get_user(user)
        repos = AuthUser(user_id=user.user_id).permissions['repositories']
        access_check = lambda r: r[1] in ['repository.read',
                                          'repository.write',
                                          'repository.admin']
        repos = [x[0] for x in filter(access_check, repos.items())]
        return Repository.query().filter(Repository.repo_name.in_(repos))

    def get_users_js(self):
        users = self.sa.query(User).filter(User.active == True).all()
        return json.dumps([
            {
             'id': u.user_id,
             'fname': u.name,
             'lname': u.lastname,
             'nname': u.username,
             'gravatar_lnk': h.gravatar_url(u.email, 14)
            } for u in users]
        )

    def get_users_groups_js(self):
        users_groups = self.sa.query(UserGroup)\
            .filter(UserGroup.users_group_active == True).all()
        users_groups = UserGroupList(users_groups, perm_set=['usergroup.read',
                                                             'usergroup.write',
                                                             'usergroup.admin'])
        return json.dumps([
            {
             'id': gr.users_group_id,
             'grname': gr.users_group_name,
             'grmembers': len(gr.members),
            } for gr in users_groups]
        )

    @classmethod
    def _render_datatable(cls, tmpl, *args, **kwargs):
        import rhodecode
        from pylons import tmpl_context as c
        from pylons.i18n.translation import _

        _tmpl_lookup = rhodecode.CONFIG['pylons.app_globals'].mako_lookup
        template = _tmpl_lookup.get_template('data_table/_dt_elements.html')

        tmpl = template.get_def(tmpl)
        kwargs.update(dict(_=_, h=h, c=c))
        return tmpl.render(*args, **kwargs)

    @classmethod
    def update_repoinfo(cls, repositories=None):
        if not repositories:
            repositories = Repository.getAll()
        for repo in repositories:
            repo.update_changeset_cache()

    def get_repos_as_dict(self, repos_list=None, admin=False, perm_check=True,
                          super_user_actions=False):
        _render = self._render_datatable
        from pylons import tmpl_context as c

        def quick_menu(repo_name):
            return _render('quick_menu', repo_name)

        def repo_lnk(name, rtype, private, fork_of):
            return _render('repo_name', name, rtype, private, fork_of,
                           short_name=not admin, admin=False)

        def last_change(last_change):
            return _render("last_change", last_change)

        def rss_lnk(repo_name):
            return _render("rss", repo_name)

        def atom_lnk(repo_name):
            return _render("atom", repo_name)

        def last_rev(repo_name, cs_cache):
            return _render('revision', repo_name, cs_cache.get('revision'),
                           cs_cache.get('raw_id'), cs_cache.get('author'),
                           cs_cache.get('message'))

        def desc(desc):
            if c.visual.stylify_metatags:
                return h.urlify_text(h.desc_stylize(h.truncate(desc, 60)))
            else:
                return h.urlify_text(h.truncate(desc, 60))

        def repo_actions(repo_name):
            return _render('repo_actions', repo_name, super_user_actions)

        def owner_actions(user_id, username):
            return _render('user_name', user_id, username)

        repos_data = []
        for repo in repos_list:
            if perm_check:
                # check permission at this level
                if not HasRepoPermissionAny(
                    'repository.read', 'repository.write', 'repository.admin'
                )(repo.repo_name, 'get_repos_as_dict check'):
                    continue
            cs_cache = repo.changeset_cache
            row = {
                "menu": quick_menu(repo.repo_name),
                "raw_name": repo.repo_name.lower(),
                "name": repo_lnk(repo.repo_name, repo.repo_type,
                                 repo.private, repo.fork),
                "last_change": last_change(repo.last_db_change),
                "last_changeset": last_rev(repo.repo_name, cs_cache),
                "raw_tip": cs_cache.get('revision'),
                "desc": desc(repo.description),
                "owner": h.person(repo.user.username),
                "rss": rss_lnk(repo.repo_name),
                "atom": atom_lnk(repo.repo_name),

            }
            if admin:
                row.update({
                    "action": repo_actions(repo.repo_name),
                    "owner": owner_actions(repo.user.user_id,
                                           h.person(repo.user.username))
                })
            repos_data.append(row)

        return {
            "totalRecords": len(repos_list),
            "startIndex": 0,
            "sort": "name",
            "dir": "asc",
            "records": repos_data
        }

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
        group, repo_name, repo_name_full = repo_info.groups_and_repo
        defaults['repo_name'] = repo_name
        defaults['repo_group'] = getattr(group[-1] if group else None,
                                         'group_id', None)

        for strip, k in [(0, 'repo_type'), (1, 'repo_enable_downloads'),
                  (1, 'repo_description'), (1, 'repo_enable_locking'),
                  (1, 'repo_landing_rev'), (0, 'clone_uri'),
                  (1, 'repo_private'), (1, 'repo_enable_statistics')]:
            attr = k
            if strip:
                attr = remove_prefix(k, 'repo_')

            defaults[k] = defaults[attr]

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

    def update(self, org_repo_name, **kwargs):
        try:
            cur_repo = self.get_by_repo_name(org_repo_name, cache=False)

            if 'user' in kwargs:
                cur_repo.user = User.get_by_username(kwargs['user'])

            if 'repo_group' in kwargs:
                cur_repo.group = RepoGroup.get(kwargs['repo_group'])

            for strip, k in [(0, 'repo_type'), (1, 'repo_enable_downloads'),
                      (1, 'repo_description'), (1, 'repo_enable_locking'),
                      (1, 'repo_landing_rev'), (0, 'clone_uri'),
                      (1, 'repo_private'), (1, 'repo_enable_statistics')]:
                if k in kwargs:
                    val = kwargs[k]
                    if strip:
                        k = remove_prefix(k, 'repo_')
                    setattr(cur_repo, k, val)

            new_name = cur_repo.get_new_name(kwargs['repo_name'])
            cur_repo.repo_name = new_name
            #if private flag is set, reset default permission to NONE

            if kwargs.get('repo_private'):
                EMPTY_PERM = 'repository.none'
                RepoModel().grant_user_permission(
                    repo=cur_repo, user='default', perm=EMPTY_PERM
                )
            #handle extra fields
            for field in filter(lambda k: k.startswith(RepositoryField.PREFIX), kwargs):
                k = RepositoryField.un_prefix_key(field)
                ex_field = RepositoryField.get_by_key_name(key=k, repo=cur_repo)
                if ex_field:
                    ex_field.field_value = kwargs[field]
                    self.sa.add(ex_field)
            self.sa.add(cur_repo)

            if org_repo_name != new_name:
                # rename repository
                self.__rename_repo(old=org_repo_name, new=new_name)

            return cur_repo
        except Exception:
            log.error(traceback.format_exc())
            raise

    def create_repo(self, repo_name, repo_type, description, owner,
                    private=False, clone_uri=None, repos_group=None,
                    landing_rev='tip', just_db=False, fork_of=None,
                    copy_fork_permissions=False, enable_statistics=False,
                    enable_locking=False, enable_downloads=False):
        """
        Create repository

        """
        from rhodecode.model.scm import ScmModel

        owner = self._get_user(owner)
        fork_of = self._get_repo(fork_of)
        repos_group = self._get_repo_group(repos_group)
        try:

            # repo name is just a name of repository
            # while repo_name_full is a full qualified name that is combined
            # with name and path of group
            repo_name_full = repo_name
            repo_name = repo_name.split(self.URL_SEPARATOR)[-1]

            new_repo = Repository()
            new_repo.enable_statistics = False
            new_repo.repo_name = repo_name_full
            new_repo.repo_type = repo_type
            new_repo.user = owner
            new_repo.group = repos_group
            new_repo.description = description or repo_name
            new_repo.private = private
            new_repo.clone_uri = clone_uri
            new_repo.landing_rev = landing_rev

            new_repo.enable_statistics = enable_statistics
            new_repo.enable_locking = enable_locking
            new_repo.enable_downloads = enable_downloads

            if repos_group:
                new_repo.enable_locking = repos_group.enable_locking

            if fork_of:
                parent_repo = fork_of
                new_repo.fork = parent_repo

            self.sa.add(new_repo)

            if fork_of:
                if copy_fork_permissions:
                    repo = fork_of
                    user_perms = UserRepoToPerm.query()\
                        .filter(UserRepoToPerm.repository == repo).all()
                    group_perms = UserGroupRepoToPerm.query()\
                        .filter(UserGroupRepoToPerm.repository == repo).all()

                    for perm in user_perms:
                        UserRepoToPerm.create(perm.user, new_repo,
                                              perm.permission)

                    for perm in group_perms:
                        UserGroupRepoToPerm.create(perm.users_group, new_repo,
                                                    perm.permission)
                else:
                    perm_obj = self._create_default_perms(new_repo, private)
                    self.sa.add(perm_obj)
            else:
                perm_obj = self._create_default_perms(new_repo, private)
                self.sa.add(perm_obj)

            if not just_db:
                self.__create_repo(repo_name, repo_type,
                                   repos_group,
                                   clone_uri)
                log_create_repository(new_repo.get_dict(),
                                      created_by=owner.username)

            # now automatically start following this repository as owner
            ScmModel(self.sa).toggle_following_repo(new_repo.repo_id,
                                                    owner.user_id)
            return new_repo
        except Exception:
            log.error(traceback.format_exc())
            raise

    def create(self, form_data, cur_user, just_db=False, fork=None):
        """
        Backward compatibility function, just a wrapper on top of create_repo

        :param form_data:
        :param cur_user:
        :param just_db:
        :param fork:
        """
        owner = cur_user
        repo_name = form_data['repo_name_full']
        repo_type = form_data['repo_type']
        description = form_data['repo_description']
        private = form_data['repo_private']
        clone_uri = form_data.get('clone_uri')
        repos_group = form_data['repo_group']
        landing_rev = form_data['repo_landing_rev']
        copy_fork_permissions = form_data.get('copy_permissions')
        fork_of = form_data.get('fork_parent_id')

        ## repo creation defaults, private and repo_type are filled in form
        defs = RhodeCodeSetting.get_default_repo_settings(strip_prefix=True)
        enable_statistics = defs.get('repo_enable_statistics')
        enable_locking = defs.get('repo_enable_locking')
        enable_downloads = defs.get('repo_enable_downloads')

        return self.create_repo(
            repo_name, repo_type, description, owner, private, clone_uri,
            repos_group, landing_rev, just_db, fork_of, copy_fork_permissions,
            enable_statistics, enable_locking, enable_downloads
        )

    def _update_permissions(self, repo, perms_new=None, perms_updates=None,
                            check_perms=True):
        if not perms_new:
            perms_new = []
        if not perms_updates:
            perms_updates = []

        # update permissions
        for member, perm, member_type in perms_updates:
            if member_type == 'user':
                # this updates existing one
                self.grant_user_permission(
                    repo=repo, user=member, perm=perm
                )
            else:
                #check if we have permissions to alter this usergroup
                req_perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin')
                if not check_perms or HasUserGroupPermissionAny(*req_perms)(member):
                    self.grant_users_group_permission(
                        repo=repo, group_name=member, perm=perm
                    )
        # set new permissions
        for member, perm, member_type in perms_new:
            if member_type == 'user':
                self.grant_user_permission(
                    repo=repo, user=member, perm=perm
                )
            else:
                #check if we have permissions to alter this usergroup
                req_perms = ('usergroup.read', 'usergroup.write', 'usergroup.admin')
                if not check_perms or HasUserGroupPermissionAny(*req_perms)(member):
                    self.grant_users_group_permission(
                        repo=repo, group_name=member, perm=perm
                    )

    def create_fork(self, form_data, cur_user):
        """
        Simple wrapper into executing celery task for fork creation

        :param form_data:
        :param cur_user:
        """
        from rhodecode.lib.celerylib import tasks, run_task
        run_task(tasks.create_repo_fork, form_data, cur_user)

    def delete(self, repo, forks=None, fs_remove=True):
        """
        Delete given repository, forks parameter defines what do do with
        attached forks. Throws AttachedForksError if deleted repo has attached
        forks

        :param repo:
        :param forks: str 'delete' or 'detach'
        :param fs_remove: remove(archive) repo from filesystem
        """
        repo = self._get_repo(repo)
        if repo:
            if forks == 'detach':
                for r in repo.forks:
                    r.fork = None
                    self.sa.add(r)
            elif forks == 'delete':
                for r in repo.forks:
                    self.delete(r, forks='delete')
            elif [f for f in repo.forks]:
                raise AttachedForksError()

            old_repo_dict = repo.get_dict()
            owner = repo.user
            try:
                self.sa.delete(repo)
                if fs_remove:
                    self.__delete_repo(repo)
                else:
                    log.debug('skipping removal from filesystem')
                log_delete_repository(old_repo_dict,
                                      deleted_by=owner.username)
            except Exception:
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
        user = self._get_user(user)
        repo = self._get_repo(repo)
        permission = self._get_perm(perm)

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
        log.debug('Granted perm %s to %s on %s' % (perm, user, repo))

    def revoke_user_permission(self, repo, user):
        """
        Revoke permission for user on given repository

        :param repo: Instance of Repository, repository_id, or repository name
        :param user: Instance of User, user_id or username
        """

        user = self._get_user(user)
        repo = self._get_repo(repo)

        obj = self.sa.query(UserRepoToPerm)\
            .filter(UserRepoToPerm.repository == repo)\
            .filter(UserRepoToPerm.user == user)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm on %s on %s' % (repo, user))

    def grant_users_group_permission(self, repo, group_name, perm):
        """
        Grant permission for user group on given repository, or update
        existing one if found

        :param repo: Instance of Repository, repository_id, or repository name
        :param group_name: Instance of UserGroup, users_group_id,
            or user group name
        :param perm: Instance of Permission, or permission_name
        """
        repo = self._get_repo(repo)
        group_name = self._get_user_group(group_name)
        permission = self._get_perm(perm)

        # check if we have that permission already
        obj = self.sa.query(UserGroupRepoToPerm)\
            .filter(UserGroupRepoToPerm.users_group == group_name)\
            .filter(UserGroupRepoToPerm.repository == repo)\
            .scalar()

        if obj is None:
            # create new
            obj = UserGroupRepoToPerm()

        obj.repository = repo
        obj.users_group = group_name
        obj.permission = permission
        self.sa.add(obj)
        log.debug('Granted perm %s to %s on %s' % (perm, group_name, repo))

    def revoke_users_group_permission(self, repo, group_name):
        """
        Revoke permission for user group on given repository

        :param repo: Instance of Repository, repository_id, or repository name
        :param group_name: Instance of UserGroup, users_group_id,
            or user group name
        """
        repo = self._get_repo(repo)
        group_name = self._get_user_group(group_name)

        obj = self.sa.query(UserGroupRepoToPerm)\
            .filter(UserGroupRepoToPerm.repository == repo)\
            .filter(UserGroupRepoToPerm.users_group == group_name)\
            .scalar()
        if obj:
            self.sa.delete(obj)
            log.debug('Revoked perm to %s on %s' % (repo, group_name))

    def delete_stats(self, repo_name):
        """
        removes stats for given repo

        :param repo_name:
        """
        repo = self._get_repo(repo_name)
        try:
            obj = self.sa.query(Statistics)\
                    .filter(Statistics.repository == repo).scalar()
            if obj:
                self.sa.delete(obj)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def _create_repo(self, repo_name, alias, parent, clone_uri=False,
                     repo_store_location=None):
        return self.__create_repo(repo_name, alias, parent, clone_uri,
                                  repo_store_location)

    def __create_repo(self, repo_name, alias, parent, clone_uri=False,
                      repo_store_location=None):
        """
        makes repository on filesystem. It's group aware means it'll create
        a repository within a group, and alter the paths accordingly of
        group location

        :param repo_name:
        :param alias:
        :param parent_id:
        :param clone_uri:
        :param repo_path:
        """
        from rhodecode.lib.utils import is_valid_repo, is_valid_repos_group
        from rhodecode.model.scm import ScmModel

        if parent:
            new_parent_path = os.sep.join(parent.full_path_splitted)
        else:
            new_parent_path = ''
        if repo_store_location:
            _paths = [repo_store_location]
        else:
            _paths = [self.repos_path, new_parent_path, repo_name]
        # we need to make it str for mercurial
        repo_path = os.path.join(*map(lambda x: safe_str(x), _paths))

        # check if this path is not a repository
        if is_valid_repo(repo_path, self.repos_path):
            raise Exception('This path %s is a valid repository' % repo_path)

        # check if this path is a group
        if is_valid_repos_group(repo_path, self.repos_path):
            raise Exception('This path %s is a valid group' % repo_path)

        log.info('creating repo %s in %s @ %s' % (
                     repo_name, safe_unicode(repo_path),
                     obfuscate_url_pw(clone_uri)
                )
        )
        backend = get_backend(alias)
        if alias == 'hg':
            repo = backend(repo_path, create=True, src_url=clone_uri)
        elif alias == 'git':
            repo = backend(repo_path, create=True, src_url=clone_uri, bare=True)
            # add rhodecode hook into this repo
            ScmModel().install_git_hook(repo=repo)
        else:
            raise Exception('Undefined alias %s' % alias)
        return repo

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
        # disable hg/git internal that it doesn't get detected as repo
        alias = repo.repo_type

        bare = getattr(repo.scm_instance, 'bare', False)

        if not bare:
            # skip this for bare git repos
            shutil.move(os.path.join(rm_path, '.%s' % alias),
                        os.path.join(rm_path, 'rm__.%s' % alias))
        # disable repo
        _now = datetime.now()
        _ms = str(_now.microsecond).rjust(6, '0')
        _d = 'rm__%s__%s' % (_now.strftime('%Y%m%d_%H%M%S_' + _ms),
                             repo.just_name)
        if repo.group:
            args = repo.group.full_path_splitted + [_d]
            _d = os.path.join(*args)
        shutil.move(rm_path, os.path.join(self.repos_path, _d))
