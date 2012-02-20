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
import os
import time
import traceback
import logging
import cStringIO

from rhodecode.lib.vcs import get_backend
from rhodecode.lib.vcs.exceptions import RepositoryError
from rhodecode.lib.vcs.utils.lazy import LazyProperty
from rhodecode.lib.vcs.nodes import FileNode

from rhodecode import BACKENDS
from rhodecode.lib import helpers as h
from rhodecode.lib import safe_str
from rhodecode.lib.auth import HasRepoPermissionAny, HasReposGroupPermissionAny
from rhodecode.lib.utils import get_repos as get_filesystem_repos, make_ui, \
    action_logger, EmptyChangeset
from rhodecode.model import BaseModel
from rhodecode.model.db import Repository, RhodeCodeUi, CacheInvalidation, \
    UserFollowing, UserLog, User, RepoGroup

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

    def __init__(self, db_repo_list, repos_path, order_by=None):
        self.db_repo_list = db_repo_list
        self.repos_path = repos_path
        self.order_by = order_by
        self.reversed = (order_by or '').startswith('-')

    def __len__(self):
        return len(self.db_repo_list)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.__len__())

    def __iter__(self):
        for dbr in self.db_repo_list:
            scmr = dbr.scm_instance_cached
            # check permission at this level
            if not HasRepoPermissionAny(
                'repository.read', 'repository.write', 'repository.admin'
            )(dbr.repo_name, 'get repo check'):
                continue

            if scmr is None:
                log.error(
                    '%s this repository is present in database but it '
                    'cannot be created as an scm instance' % dbr.repo_name
                )
                continue

            last_change = scmr.last_change
            tip = h.get_changeset_safe(scmr, 'tip')

            tmp_d = {}
            tmp_d['name'] = dbr.repo_name
            tmp_d['name_sort'] = tmp_d['name'].lower()
            tmp_d['description'] = dbr.description
            tmp_d['description_sort'] = tmp_d['description']
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


class GroupList(object):

    def __init__(self, db_repo_group_list):
        self.db_repo_group_list = db_repo_group_list

    def __len__(self):
        return len(self.db_repo_group_list)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.__len__())

    def __iter__(self):
        for dbgr in self.db_repo_group_list:
            # check permission at this level
            if not HasReposGroupPermissionAny(
                'group.read', 'group.write', 'group.admin'
            )(dbgr.group_name, 'get group repo check'):
                continue

            yield dbgr


class ScmModel(BaseModel):
    """
    Generic Scm Model
    """

    def __get_repo(self, instance):
        cls = Repository
        if isinstance(instance, cls):
            return instance
        elif isinstance(instance, int) or str(instance).isdigit():
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
            name = Repository.url_sep().join(name.split(os.sep))

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

        return repos

    def get_repos(self, all_repos=None, sort_key=None):
        """
        Get all repos from db and for each repo create it's
        backend instance and fill that backed with information from database

        :param all_repos: list of repository names as strings
            give specific repositories list, good for filtering
        """
        if all_repos is None:
            all_repos = self.sa.query(Repository)\
                        .filter(Repository.group_id == None)\
                        .order_by(Repository.repo_name).all()

        repo_iter = CachedRepoList(all_repos, repos_path=self.repos_path,
                                   order_by=sort_key)

        return repo_iter

    def get_repos_groups(self, all_groups=None):
        if all_groups is None:
            all_groups = RepoGroup.query()\
                .filter(RepoGroup.group_parent_id == None).all()
        group_iter = GroupList(all_groups)

        return group_iter

    def mark_for_invalidation(self, repo_name):
        """Puts cache invalidation task into db for
        further global cache invalidation

        :param repo_name: this repo that should invalidation take place
        """
        CacheInvalidation.set_invalidate(repo_name)
        CacheInvalidation.set_invalidate(repo_name + "_README")

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
            except:
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
        except:
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
            except:
                log.error(traceback.format_exc())
                raise

        try:
            f = UserFollowing()
            f.user_id = user_id
            f.follows_user_id = follow_user_id
            self.sa.add(f)
        except:
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

    def get_followers(self, repo_id):
        if not isinstance(repo_id, int):
            repo_id = getattr(Repository.get_by_repo_name(repo_id), 'repo_id')

        return self.sa.query(UserFollowing)\
                .filter(UserFollowing.follows_repo_id == repo_id).count()

    def get_forks(self, repo_id):
        if not isinstance(repo_id, int):
            repo_id = getattr(Repository.get_by_repo_name(repo_id), 'repo_id')

        return self.sa.query(Repository)\
                .filter(Repository.fork_id == repo_id).count()

    def mark_as_fork(self, repo, fork, user):
        repo = self.__get_repo(repo)
        fork = self.__get_repo(fork)
        repo.fork = fork
        self.sa.add(repo)
        return repo

    def pull_changes(self, repo_name, username):
        dbrepo = Repository.get_by_repo_name(repo_name)
        clone_uri = dbrepo.clone_uri
        if not clone_uri:
            raise Exception("This repository doesn't have a clone uri")

        repo = dbrepo.scm_instance
        try:
            extras = {'ip': '',
                      'username': username,
                      'action': 'push_remote',
                      'repository': repo_name}

            #inject ui extra param to log this action via push logger
            for k, v in extras.items():
                repo._repo.ui.setconfig('rhodecode_extras', k, v)

            repo.pull(clone_uri)
            self.mark_for_invalidation(repo_name)
        except:
            log.error(traceback.format_exc())
            raise

    def commit_change(self, repo, repo_name, cs, user, author, message,
                      content, f_path):

        if repo.alias == 'hg':
            from rhodecode.lib.vcs.backends.hg import MercurialInMemoryChangeset as IMC
        elif repo.alias == 'git':
            from rhodecode.lib.vcs.backends.git import GitInMemoryChangeset as IMC

        # decoding here will force that we have proper encoded values
        # in any other case this will throw exceptions and deny commit
        content = safe_str(content)
        message = safe_str(message)
        path = safe_str(f_path)
        author = safe_str(author)
        m = IMC(repo)
        m.change(FileNode(path, content))
        tip = m.commit(message=message,
                 author=author,
                 parents=[cs], branch=cs.branch)

        new_cs = tip.short_id
        action = 'push_local:%s' % new_cs

        action_logger(user, action, repo_name)

        self.mark_for_invalidation(repo_name)

    def create_node(self, repo, repo_name, cs, user, author, message, content,
                      f_path):
        if repo.alias == 'hg':
            from rhodecode.lib.vcs.backends.hg import MercurialInMemoryChangeset as IMC
        elif repo.alias == 'git':
            from rhodecode.lib.vcs.backends.git import GitInMemoryChangeset as IMC
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

        message = safe_str(message)
        path = safe_str(f_path)
        author = safe_str(author)
        m = IMC(repo)

        if isinstance(cs, EmptyChangeset):
            # Emptychangeset means we we're editing empty repository
            parents = None
        else:
            parents = [cs]

        m.add(FileNode(path, content=content))
        tip = m.commit(message=message,
                 author=author,
                 parents=parents, branch=cs.branch)
        new_cs = tip.short_id
        action = 'push_local:%s' % new_cs

        action_logger(user, action, repo_name)

        self.mark_for_invalidation(repo_name)

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
