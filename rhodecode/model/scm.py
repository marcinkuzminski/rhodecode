# -*- coding: utf-8 -*-
"""
    rhodecode.model.scm
    ~~~~~~~~~~~~~~~~~~~

    Scm model for RhodeCode

    :created_on: Apr 9, 2010
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
import re
import time
import traceback
import logging
import cStringIO
import pkg_resources
from os.path import dirname as dn, join as jn

from sqlalchemy import func
from pylons.i18n.translation import _

import rhodecode
from rhodecode.lib.vcs import get_backend
from rhodecode.lib.vcs.exceptions import RepositoryError
from rhodecode.lib.vcs.utils.lazy import LazyProperty
from rhodecode.lib.vcs.nodes import FileNode
from rhodecode.lib.vcs.backends.base import EmptyChangeset

from rhodecode import BACKENDS
from rhodecode.lib import helpers as h
from rhodecode.lib.utils2 import safe_str, safe_unicode, get_server_url,\
    _set_extras
from rhodecode.lib.auth import HasRepoPermissionAny, HasReposGroupPermissionAny,\
    HasUserGroupPermissionAnyDecorator, HasUserGroupPermissionAny
from rhodecode.lib.utils import get_filesystem_repos, make_ui, \
    action_logger, REMOVED_REPO_PAT
from rhodecode.model import BaseModel
from rhodecode.model.db import Repository, RhodeCodeUi, CacheInvalidation, \
    UserFollowing, UserLog, User, RepoGroup, PullRequest
from rhodecode.lib.hooks import log_push_action
from rhodecode.lib.exceptions import NonRelativePathError

log = logging.getLogger(__name__)


class UserTemp(object):
    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return "<%s('id:%s')>" % (self.__class__.__name__, self.user_id)


class RepoTemp(object):
    def __init__(self, repo_id):
        self.repo_id = repo_id

    def __repr__(self):
        return "<%s('id:%s')>" % (self.__class__.__name__, self.repo_id)


class CachedRepoList(object):
    """
    Cached repo list, uses in-memory cache after initialization, that is
    super fast
    """

    def __init__(self, db_repo_list, repos_path, order_by=None, perm_set=None):
        self.db_repo_list = db_repo_list
        self.repos_path = repos_path
        self.order_by = order_by
        self.reversed = (order_by or '').startswith('-')
        if not perm_set:
            perm_set = ['repository.read', 'repository.write',
                        'repository.admin']
        self.perm_set = perm_set

    def __len__(self):
        return len(self.db_repo_list)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.__len__())

    def __iter__(self):
        # pre-propagated valid_cache_keys to save executing select statements
        # for each repo
        valid_cache_keys = CacheInvalidation.get_valid_cache_keys()

        for dbr in self.db_repo_list:
            scmr = dbr.scm_instance_cached(valid_cache_keys)
            # check permission at this level
            if not HasRepoPermissionAny(
                *self.perm_set)(dbr.repo_name, 'get repo check'):
                continue

            try:
                last_change = scmr.last_change
                tip = h.get_changeset_safe(scmr, 'tip')
            except Exception:
                log.error(
                    '%s this repository is present in database but it '
                    'cannot be created as an scm instance, org_exc:%s'
                    % (dbr.repo_name, traceback.format_exc())
                )
                continue

            tmp_d = {}
            tmp_d['name'] = dbr.repo_name
            tmp_d['name_sort'] = tmp_d['name'].lower()
            tmp_d['raw_name'] = tmp_d['name'].lower()
            tmp_d['description'] = dbr.description
            tmp_d['description_sort'] = tmp_d['description'].lower()
            tmp_d['last_change'] = last_change
            tmp_d['last_change_sort'] = time.mktime(last_change.timetuple())
            tmp_d['tip'] = tip.raw_id
            tmp_d['tip_sort'] = tip.revision
            tmp_d['rev'] = tip.revision
            tmp_d['contact'] = dbr.user.full_contact
            tmp_d['contact_sort'] = tmp_d['contact']
            tmp_d['owner_sort'] = tmp_d['contact']
            tmp_d['repo_archives'] = list(scmr._get_archives())
            tmp_d['last_msg'] = tip.message
            tmp_d['author'] = tip.author
            tmp_d['dbrepo'] = dbr.get_dict()
            tmp_d['dbrepo_fork'] = dbr.fork.get_dict() if dbr.fork else {}
            yield tmp_d


class SimpleCachedRepoList(CachedRepoList):
    """
    Lighter version of CachedRepoList without the scm initialisation
    """

    def __iter__(self):
        for dbr in self.db_repo_list:
            # check permission at this level
            if not HasRepoPermissionAny(
                *self.perm_set)(dbr.repo_name, 'get repo check'):
                continue

            tmp_d = {}
            tmp_d['name'] = dbr.repo_name
            tmp_d['name_sort'] = tmp_d['name'].lower()
            tmp_d['raw_name'] = tmp_d['name'].lower()
            tmp_d['description'] = dbr.description
            tmp_d['description_sort'] = tmp_d['description'].lower()
            tmp_d['dbrepo'] = dbr.get_dict()
            tmp_d['dbrepo_fork'] = dbr.fork.get_dict() if dbr.fork else {}
            yield tmp_d


class _PermCheckIterator(object):
    def __init__(self, obj_list, obj_attr, perm_set, perm_checker):
        """
        Creates iterator from given list of objects, additionally
        checking permission for them from perm_set var

        :param obj_list: list of db objects
        :param obj_attr: attribute of object to pass into perm_checker
        :param perm_set: list of permissions to check
        :param perm_checker: callable to check permissions against
        """
        self.obj_list = obj_list
        self.obj_attr = obj_attr
        self.perm_set = perm_set
        self.perm_checker = perm_checker

    def __len__(self):
        return len(self.obj_list)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.__len__())

    def __iter__(self):
        for db_obj in self.obj_list:
            # check permission at this level
            name = getattr(db_obj, self.obj_attr, None)
            if not self.perm_checker(*self.perm_set)(name, self.__class__.__name__):
                continue

            yield db_obj


class RepoList(_PermCheckIterator):

    def __init__(self, db_repo_list, perm_set=None):
        if not perm_set:
            perm_set = ['repository.read', 'repository.write', 'repository.admin']

        super(RepoList, self).__init__(obj_list=db_repo_list,
                    obj_attr='repo_name', perm_set=perm_set,
                    perm_checker=HasRepoPermissionAny)


class RepoGroupList(_PermCheckIterator):

    def __init__(self, db_repo_group_list, perm_set=None):
        if not perm_set:
            perm_set = ['group.read', 'group.write', 'group.admin']

        super(RepoGroupList, self).__init__(obj_list=db_repo_group_list,
                    obj_attr='group_name', perm_set=perm_set,
                    perm_checker=HasReposGroupPermissionAny)


class UserGroupList(_PermCheckIterator):

    def __init__(self, db_user_group_list, perm_set=None):
        if not perm_set:
            perm_set = ['usergroup.read', 'usergroup.write', 'usergroup.admin']

        super(UserGroupList, self).__init__(obj_list=db_user_group_list,
                    obj_attr='users_group_name', perm_set=perm_set,
                    perm_checker=HasUserGroupPermissionAny)


class ScmModel(BaseModel):
    """
    Generic Scm Model
    """

    def __get_repo(self, instance):
        cls = Repository
        if isinstance(instance, cls):
            return instance
        elif isinstance(instance, int) or safe_str(instance).isdigit():
            return cls.get(instance)
        elif isinstance(instance, basestring):
            return cls.get_by_repo_name(instance)
        elif instance:
            raise Exception('given object must be int, basestr or Instance'
                            ' of %s got %s' % (type(cls), type(instance)))

    @LazyProperty
    def repos_path(self):
        """
        Get's the repositories root path from database
        """

        q = self.sa.query(RhodeCodeUi).filter(RhodeCodeUi.ui_key == '/').one()

        return q.ui_value

    def repo_scan(self, repos_path=None):
        """
        Listing of repositories in given path. This path should not be a
        repository itself. Return a dictionary of repository objects

        :param repos_path: path to directory containing repositories
        """

        if repos_path is None:
            repos_path = self.repos_path

        log.info('scanning for repositories in %s' % repos_path)

        baseui = make_ui('db')
        repos = {}

        for name, path in get_filesystem_repos(repos_path, recursive=True):
            # name need to be decomposed and put back together using the /
            # since this is internal storage separator for rhodecode
            name = Repository.normalize_repo_name(name)

            try:
                if name in repos:
                    raise RepositoryError('Duplicate repository name %s '
                                          'found in %s' % (name, path))
                else:

                    klass = get_backend(path[0])

                    if path[0] == 'hg' and path[0] in BACKENDS.keys():
                        repos[name] = klass(safe_str(path[1]), baseui=baseui)

                    if path[0] == 'git' and path[0] in BACKENDS.keys():
                        repos[name] = klass(path[1])
            except OSError:
                continue
        log.debug('found %s paths with repositories' % (len(repos)))
        return repos

    def get_repos(self, all_repos=None, sort_key=None, simple=False):
        """
        Get all repos from db and for each repo create it's
        backend instance and fill that backed with information from database

        :param all_repos: list of repository names as strings
            give specific repositories list, good for filtering

        :param sort_key: initial sorting of repos
        :param simple: use SimpleCachedList - one without the SCM info
        """
        if all_repos is None:
            all_repos = self.sa.query(Repository)\
                        .filter(Repository.group_id == None)\
                        .order_by(func.lower(Repository.repo_name)).all()
        if simple:
            repo_iter = SimpleCachedRepoList(all_repos,
                                             repos_path=self.repos_path,
                                             order_by=sort_key)
        else:
            repo_iter = CachedRepoList(all_repos,
                                       repos_path=self.repos_path,
                                       order_by=sort_key)

        return repo_iter

    def get_repos_groups(self, all_groups=None):
        if all_groups is None:
            all_groups = RepoGroup.query()\
                .filter(RepoGroup.group_parent_id == None).all()
        return [x for x in RepoGroupList(all_groups)]

    def mark_for_invalidation(self, repo_name):
        """
        Mark caches of this repo invalid in the database.

        :param repo_name: the repo for which caches should be marked invalid
        """
        CacheInvalidation.set_invalidate(repo_name)
        repo = Repository.get_by_repo_name(repo_name)
        if repo:
            repo.update_changeset_cache()

    def toggle_following_repo(self, follow_repo_id, user_id):

        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_repo_id == follow_repo_id)\
            .filter(UserFollowing.user_id == user_id).scalar()

        if f is not None:
            try:
                self.sa.delete(f)
                action_logger(UserTemp(user_id),
                              'stopped_following_repo',
                              RepoTemp(follow_repo_id))
                return
            except Exception:
                log.error(traceback.format_exc())
                raise

        try:
            f = UserFollowing()
            f.user_id = user_id
            f.follows_repo_id = follow_repo_id
            self.sa.add(f)

            action_logger(UserTemp(user_id),
                          'started_following_repo',
                          RepoTemp(follow_repo_id))
        except Exception:
            log.error(traceback.format_exc())
            raise

    def toggle_following_user(self, follow_user_id, user_id):
        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_user_id == follow_user_id)\
            .filter(UserFollowing.user_id == user_id).scalar()

        if f is not None:
            try:
                self.sa.delete(f)
                return
            except Exception:
                log.error(traceback.format_exc())
                raise

        try:
            f = UserFollowing()
            f.user_id = user_id
            f.follows_user_id = follow_user_id
            self.sa.add(f)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def is_following_repo(self, repo_name, user_id, cache=False):
        r = self.sa.query(Repository)\
            .filter(Repository.repo_name == repo_name).scalar()

        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_repository == r)\
            .filter(UserFollowing.user_id == user_id).scalar()

        return f is not None

    def is_following_user(self, username, user_id, cache=False):
        u = User.get_by_username(username)

        f = self.sa.query(UserFollowing)\
            .filter(UserFollowing.follows_user == u)\
            .filter(UserFollowing.user_id == user_id).scalar()

        return f is not None

    def get_followers(self, repo):
        repo = self._get_repo(repo)

        return self.sa.query(UserFollowing)\
                .filter(UserFollowing.follows_repository == repo).count()

    def get_forks(self, repo):
        repo = self._get_repo(repo)
        return self.sa.query(Repository)\
                .filter(Repository.fork == repo).count()

    def get_pull_requests(self, repo):
        repo = self._get_repo(repo)
        return self.sa.query(PullRequest)\
                .filter(PullRequest.other_repo == repo)\
                .filter(PullRequest.status != PullRequest.STATUS_CLOSED).count()

    def mark_as_fork(self, repo, fork, user):
        repo = self.__get_repo(repo)
        fork = self.__get_repo(fork)
        if fork and repo.repo_id == fork.repo_id:
            raise Exception("Cannot set repository as fork of itself")
        repo.fork = fork
        self.sa.add(repo)
        return repo

    def _handle_rc_scm_extras(self, username, repo_name, repo_alias,
                              action=None):
        from rhodecode import CONFIG
        from rhodecode.lib.base import _get_ip_addr
        try:
            from pylons import request
            environ = request.environ
        except TypeError:
            # we might use this outside of request context, let's fake the
            # environ data
            from webob import Request
            environ = Request.blank('').environ
        extras = {
            'ip': _get_ip_addr(environ),
            'username': username,
            'action': action or 'push_local',
            'repository': repo_name,
            'scm': repo_alias,
            'config': CONFIG['__file__'],
            'server_url': get_server_url(environ),
            'make_lock': None,
            'locked_by': [None, None]
        }
        _set_extras(extras)

    def _handle_push(self, repo, username, action, repo_name, revisions):
        """
        Triggers push action hooks

        :param repo: SCM repo
        :param username: username who pushes
        :param action: push/push_loca/push_remote
        :param repo_name: name of repo
        :param revisions: list of revisions that we pushed
        """
        self._handle_rc_scm_extras(username, repo_name, repo_alias=repo.alias)
        _scm_repo = repo._repo
        # trigger push hook
        if repo.alias == 'hg':
            log_push_action(_scm_repo.ui, _scm_repo, node=revisions[0])
        elif repo.alias == 'git':
            log_push_action(None, _scm_repo, _git_revs=revisions)

    def _get_IMC_module(self, scm_type):
        """
        Returns InMemoryCommit class based on scm_type

        :param scm_type:
        """
        if scm_type == 'hg':
            from rhodecode.lib.vcs.backends.hg import \
                MercurialInMemoryChangeset as IMC
        elif scm_type == 'git':
            from rhodecode.lib.vcs.backends.git import \
                GitInMemoryChangeset as IMC
        return IMC

    def pull_changes(self, repo, username):
        dbrepo = self.__get_repo(repo)
        clone_uri = dbrepo.clone_uri
        if not clone_uri:
            raise Exception("This repository doesn't have a clone uri")

        repo = dbrepo.scm_instance
        repo_name = dbrepo.repo_name
        try:
            if repo.alias == 'git':
                repo.fetch(clone_uri)
                # git doesn't really have something like post-fetch action
                # we fake that now. #TODO: extract fetched revisions somehow
                # here
                self._handle_push(repo,
                                  username=username,
                                  action='push_remote',
                                  repo_name=repo_name,
                                  revisions=[])
            else:
                self._handle_rc_scm_extras(username, dbrepo.repo_name,
                                           repo.alias, action='push_remote')
                repo.pull(clone_uri)

            self.mark_for_invalidation(repo_name)
        except Exception:
            log.error(traceback.format_exc())
            raise

    def commit_change(self, repo, repo_name, cs, user, author, message,
                      content, f_path):
        """
        Commits changes

        :param repo: SCM instance

        """
        user = self._get_user(user)
        IMC = self._get_IMC_module(repo.alias)

        # decoding here will force that we have proper encoded values
        # in any other case this will throw exceptions and deny commit
        content = safe_str(content)
        path = safe_str(f_path)
        # message and author needs to be unicode
        # proper backend should then translate that into required type
        message = safe_unicode(message)
        author = safe_unicode(author)
        imc = IMC(repo)
        imc.change(FileNode(path, content, mode=cs.get_file_mode(f_path)))
        tip = imc.commit(message=message,
                       author=author,
                       parents=[cs], branch=cs.branch)

        self.mark_for_invalidation(repo_name)
        self._handle_push(repo,
                          username=user.username,
                          action='push_local',
                          repo_name=repo_name,
                          revisions=[tip.raw_id])
        return tip

    def create_nodes(self, user, repo, message, nodes, parent_cs=None,
                     author=None, trigger_push_hook=True):
        """
        Commits given multiple nodes into repo

        :param user: RhodeCode User object or user_id, the commiter
        :param repo: RhodeCode Repository object
        :param message: commit message
        :param nodes: mapping {filename:{'content':content},...}
        :param parent_cs: parent changeset, can be empty than it's initial commit
        :param author: author of commit, cna be different that commiter only for git
        :param trigger_push_hook: trigger push hooks

        :returns: new commited changeset
        """

        user = self._get_user(user)
        scm_instance = repo.scm_instance_no_cache()

        processed_nodes = []
        for f_path in nodes:
            if f_path.startswith('/') or f_path.startswith('.') or '../' in f_path:
                raise NonRelativePathError('%s is not an relative path' % f_path)
            if f_path:
                f_path = os.path.normpath(f_path)
            f_path = safe_str(f_path)
            content = nodes[f_path]['content']
            # decoding here will force that we have proper encoded values
            # in any other case this will throw exceptions and deny commit
            if isinstance(content, (basestring,)):
                content = safe_str(content)
            elif isinstance(content, (file, cStringIO.OutputType,)):
                content = content.read()
            else:
                raise Exception('Content is of unrecognized type %s' % (
                    type(content)
                ))
            processed_nodes.append((f_path, content))

        message = safe_unicode(message)
        commiter = user.full_contact
        author = safe_unicode(author) if author else commiter

        IMC = self._get_IMC_module(scm_instance.alias)
        imc = IMC(scm_instance)

        if not parent_cs:
            parent_cs = EmptyChangeset(alias=scm_instance.alias)

        if isinstance(parent_cs, EmptyChangeset):
            # EmptyChangeset means we we're editing empty repository
            parents = None
        else:
            parents = [parent_cs]
        # add multiple nodes
        for path, content in processed_nodes:
            imc.add(FileNode(path, content=content))

        tip = imc.commit(message=message,
                         author=author,
                         parents=parents,
                         branch=parent_cs.branch)

        self.mark_for_invalidation(repo.repo_name)
        if trigger_push_hook:
            self._handle_push(scm_instance,
                              username=user.username,
                              action='push_local',
                              repo_name=repo.repo_name,
                              revisions=[tip.raw_id])
        return tip

    def get_nodes(self, repo_name, revision, root_path='/', flat=True):
        """
        recursive walk in root dir and return a set of all path in that dir
        based on repository walk function

        :param repo_name: name of repository
        :param revision: revision for which to list nodes
        :param root_path: root path to list
        :param flat: return as a list, if False returns a dict with decription

        """
        _files = list()
        _dirs = list()
        try:
            _repo = self.__get_repo(repo_name)
            changeset = _repo.scm_instance.get_changeset(revision)
            root_path = root_path.lstrip('/')
            for topnode, dirs, files in changeset.walk(root_path):
                for f in files:
                    _files.append(f.path if flat else {"name": f.path,
                                                       "type": "file"})
                for d in dirs:
                    _dirs.append(d.path if flat else {"name": d.path,
                                                      "type": "dir"})
        except RepositoryError:
            log.debug(traceback.format_exc())
            raise

        return _dirs, _files

    def get_unread_journal(self):
        return self.sa.query(UserLog).count()

    def get_repo_landing_revs(self, repo=None):
        """
        Generates select option with tags branches and bookmarks (for hg only)
        grouped by type

        :param repo:
        """

        hist_l = []
        choices = []
        repo = self.__get_repo(repo)
        hist_l.append(['tip', _('latest tip')])
        choices.append('tip')
        if not repo:
            return choices, hist_l

        repo = repo.scm_instance

        branches_group = ([(k, k) for k, v in
                           repo.branches.iteritems()], _("Branches"))
        hist_l.append(branches_group)
        choices.extend([x[0] for x in branches_group[0]])

        if repo.alias == 'hg':
            bookmarks_group = ([(k, k) for k, v in
                                repo.bookmarks.iteritems()], _("Bookmarks"))
            hist_l.append(bookmarks_group)
            choices.extend([x[0] for x in bookmarks_group[0]])

        tags_group = ([(k, k) for k, v in
                       repo.tags.iteritems()], _("Tags"))
        hist_l.append(tags_group)
        choices.extend([x[0] for x in tags_group[0]])

        return choices, hist_l

    def install_git_hook(self, repo, force_create=False):
        """
        Creates a rhodecode hook inside a git repository

        :param repo: Instance of VCS repo
        :param force_create: Create even if same name hook exists
        """

        loc = jn(repo.path, 'hooks')
        if not repo.bare:
            loc = jn(repo.path, '.git', 'hooks')
        if not os.path.isdir(loc):
            os.makedirs(loc)

        tmpl_post = pkg_resources.resource_string(
            'rhodecode', jn('config', 'post_receive_tmpl.py')
        )
        tmpl_pre = pkg_resources.resource_string(
            'rhodecode', jn('config', 'pre_receive_tmpl.py')
        )

        for h_type, tmpl in [('pre', tmpl_pre), ('post', tmpl_post)]:
            _hook_file = jn(loc, '%s-receive' % h_type)
            _rhodecode_hook = False
            log.debug('Installing git hook in repo %s' % repo)
            if os.path.exists(_hook_file):
                # let's take a look at this hook, maybe it's rhodecode ?
                log.debug('hook exists, checking if it is from rhodecode')
                _HOOK_VER_PAT = re.compile(r'^RC_HOOK_VER')
                with open(_hook_file, 'rb') as f:
                    data = f.read()
                    matches = re.compile(r'(?:%s)\s*=\s*(.*)'
                                         % 'RC_HOOK_VER').search(data)
                    if matches:
                        try:
                            ver = matches.groups()[0]
                            log.debug('got %s it is rhodecode' % (ver))
                            _rhodecode_hook = True
                        except Exception:
                            log.error(traceback.format_exc())
            else:
                # there is no hook in this dir, so we want to create one
                _rhodecode_hook = True

            if _rhodecode_hook or force_create:
                log.debug('writing %s hook file !' % h_type)
                with open(_hook_file, 'wb') as f:
                    tmpl = tmpl.replace('_TMPL_', rhodecode.__version__)
                    f.write(tmpl)
                os.chmod(_hook_file, 0755)
            else:
                log.debug('skipping writing hook file')
