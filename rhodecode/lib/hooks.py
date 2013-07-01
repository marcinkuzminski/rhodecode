# -*- coding: utf-8 -*-
"""
    rhodecode.lib.hooks
    ~~~~~~~~~~~~~~~~~~~

    Hooks runned by rhodecode

    :created_on: Aug 6, 2010
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
import sys
import time
import binascii
import traceback
from inspect import isfunction

from rhodecode.lib.vcs.utils.hgcompat import nullrev, revrange
from rhodecode.lib import helpers as h
from rhodecode.lib.utils import action_logger
from rhodecode.lib.vcs.backends.base import EmptyChangeset
from rhodecode.lib.compat import json
from rhodecode.lib.exceptions import HTTPLockedRC, UserCreationError
from rhodecode.lib.utils2 import safe_str, _extract_extras
from rhodecode.model.db import Repository, User


def _get_scm_size(alias, root_path):

    if not alias.startswith('.'):
        alias += '.'

    size_scm, size_root = 0, 0
    for path, dirs, files in os.walk(safe_str(root_path)):
        if path.find(alias) != -1:
            for f in files:
                try:
                    size_scm += os.path.getsize(os.path.join(path, f))
                except OSError:
                    pass
        else:
            for f in files:
                try:
                    size_root += os.path.getsize(os.path.join(path, f))
                except OSError:
                    pass

    size_scm_f = h.format_byte_size(size_scm)
    size_root_f = h.format_byte_size(size_root)
    size_total_f = h.format_byte_size(size_root + size_scm)

    return size_scm_f, size_root_f, size_total_f


def repo_size(ui, repo, hooktype=None, **kwargs):
    """
    Presents size of repository after push

    :param ui:
    :param repo:
    :param hooktype:
    """

    size_hg_f, size_root_f, size_total_f = _get_scm_size('.hg', repo.root)

    last_cs = repo[len(repo) - 1]

    msg = ('Repository size .hg:%s repo:%s total:%s\n'
           'Last revision is now r%s:%s\n') % (
        size_hg_f, size_root_f, size_total_f, last_cs.rev(), last_cs.hex()[:12]
    )

    sys.stdout.write(msg)


def pre_push(ui, repo, **kwargs):
    # pre push function, currently used to ban pushing when
    # repository is locked
    ex = _extract_extras()

    usr = User.get_by_username(ex.username)
    if ex.locked_by[0] and usr.user_id != int(ex.locked_by[0]):
        locked_by = User.get(ex.locked_by[0]).username
        # this exception is interpreted in git/hg middlewares and based
        # on that proper return code is server to client
        _http_ret = HTTPLockedRC(ex.repository, locked_by)
        if str(_http_ret.code).startswith('2'):
            #2xx Codes don't raise exceptions
            sys.stdout.write(_http_ret.title)
        else:
            raise _http_ret


def pre_pull(ui, repo, **kwargs):
    # pre push function, currently used to ban pushing when
    # repository is locked
    ex = _extract_extras()
    if ex.locked_by[0]:
        locked_by = User.get(ex.locked_by[0]).username
        # this exception is interpreted in git/hg middlewares and based
        # on that proper return code is server to client
        _http_ret = HTTPLockedRC(ex.repository, locked_by)
        if str(_http_ret.code).startswith('2'):
            #2xx Codes don't raise exceptions
            sys.stdout.write(_http_ret.title)
        else:
            raise _http_ret


def log_pull_action(ui, repo, **kwargs):
    """
    Logs user last pull action

    :param ui:
    :param repo:
    """
    ex = _extract_extras()

    user = User.get_by_username(ex.username)
    action = 'pull'
    action_logger(user, action, ex.repository, ex.ip, commit=True)
    # extension hook call
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'PULL_HOOK', None)
    if isfunction(callback):
        kw = {}
        kw.update(ex)
        callback(**kw)

    if ex.make_lock is not None and ex.make_lock:
        Repository.lock(Repository.get_by_repo_name(ex.repository), user.user_id)
        #msg = 'Made lock on repo `%s`' % repository
        #sys.stdout.write(msg)

    if ex.locked_by[0]:
        locked_by = User.get(ex.locked_by[0]).username
        _http_ret = HTTPLockedRC(ex.repository, locked_by)
        if str(_http_ret.code).startswith('2'):
            #2xx Codes don't raise exceptions
            sys.stdout.write(_http_ret.title)
    return 0


def log_push_action(ui, repo, **kwargs):
    """
    Maps user last push action to new changeset id, from mercurial

    :param ui:
    :param repo: repo object containing the `ui` object
    """

    ex = _extract_extras()

    action = ex.action + ':%s'

    if ex.scm == 'hg':
        node = kwargs['node']

        def get_revs(repo, rev_opt):
            if rev_opt:
                revs = revrange(repo, rev_opt)

                if len(revs) == 0:
                    return (nullrev, nullrev)
                return (max(revs), min(revs))
            else:
                return (len(repo) - 1, 0)

        stop, start = get_revs(repo, [node + ':'])
        h = binascii.hexlify
        revs = [h(repo[r].node()) for r in xrange(start, stop + 1)]
    elif ex.scm == 'git':
        revs = kwargs.get('_git_revs', [])
        if '_git_revs' in kwargs:
            kwargs.pop('_git_revs')

    action = action % ','.join(revs)

    action_logger(ex.username, action, ex.repository, ex.ip, commit=True)

    # extension hook call
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'PUSH_HOOK', None)
    if isfunction(callback):
        kw = {'pushed_revs': revs}
        kw.update(ex)
        callback(**kw)

    if ex.make_lock is not None and not ex.make_lock:
        Repository.unlock(Repository.get_by_repo_name(ex.repository))
        msg = 'Released lock on repo `%s`\n' % ex.repository
        sys.stdout.write(msg)

    if ex.locked_by[0]:
        locked_by = User.get(ex.locked_by[0]).username
        _http_ret = HTTPLockedRC(ex.repository, locked_by)
        if str(_http_ret.code).startswith('2'):
            #2xx Codes don't raise exceptions
            sys.stdout.write(_http_ret.title)

    return 0


def log_create_repository(repository_dict, created_by, **kwargs):
    """
    Post create repository Hook. This is a dummy function for admins to re-use
    if needed. It's taken from rhodecode-extensions module and executed
    if present

    :param repository: dict dump of repository object
    :param created_by: username who created repository

    available keys of repository_dict:

     'repo_type',
     'description',
     'private',
     'created_on',
     'enable_downloads',
     'repo_id',
     'user_id',
     'enable_statistics',
     'clone_uri',
     'fork_id',
     'group_id',
     'repo_name'

    """
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'CREATE_REPO_HOOK', None)
    if isfunction(callback):
        kw = {}
        kw.update(repository_dict)
        kw.update({'created_by': created_by})
        kw.update(kwargs)
        return callback(**kw)

    return 0


def check_allowed_create_user(user_dict, created_by, **kwargs):
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'PRE_CREATE_USER_HOOK', None)
    if isfunction(callback):
        allowed, reason = callback(created_by=created_by, **user_dict)
        if not allowed:
            raise UserCreationError(reason)


def log_create_user(user_dict, created_by, **kwargs):
    """
    Post create user Hook. This is a dummy function for admins to re-use
    if needed. It's taken from rhodecode-extensions module and executed
    if present

    :param user_dict: dict dump of user object

    available keys for user_dict:

     'username',
     'full_name_or_username',
     'full_contact',
     'user_id',
     'name',
     'firstname',
     'short_contact',
     'admin',
     'lastname',
     'ip_addresses',
     'ldap_dn',
     'email',
     'api_key',
     'last_login',
     'full_name',
     'active',
     'password',
     'emails',
     'inherit_default_permissions'

    """
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'CREATE_USER_HOOK', None)
    if isfunction(callback):
        return callback(created_by=created_by, **user_dict)

    return 0


def log_delete_repository(repository_dict, deleted_by, **kwargs):
    """
    Post delete repository Hook. This is a dummy function for admins to re-use
    if needed. It's taken from rhodecode-extensions module and executed
    if present

    :param repository: dict dump of repository object
    :param deleted_by: username who deleted the repository

    available keys of repository_dict:

     'repo_type',
     'description',
     'private',
     'created_on',
     'enable_downloads',
     'repo_id',
     'user_id',
     'enable_statistics',
     'clone_uri',
     'fork_id',
     'group_id',
     'repo_name'

    """
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'DELETE_REPO_HOOK', None)
    if isfunction(callback):
        kw = {}
        kw.update(repository_dict)
        kw.update({'deleted_by': deleted_by,
                   'deleted_on': time.time()})
        kw.update(kwargs)
        return callback(**kw)

    return 0


def log_delete_user(user_dict, deleted_by, **kwargs):
    """
    Post delete user Hook. This is a dummy function for admins to re-use
    if needed. It's taken from rhodecode-extensions module and executed
    if present

    :param user_dict: dict dump of user object

    available keys for user_dict:

     'username',
     'full_name_or_username',
     'full_contact',
     'user_id',
     'name',
     'firstname',
     'short_contact',
     'admin',
     'lastname',
     'ip_addresses',
     'ldap_dn',
     'email',
     'api_key',
     'last_login',
     'full_name',
     'active',
     'password',
     'emails',
     'inherit_default_permissions'

    """
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'DELETE_USER_HOOK', None)
    if isfunction(callback):
        return callback(deleted_by=deleted_by, **user_dict)

    return 0


handle_git_pre_receive = (lambda repo_path, revs, env:
    handle_git_receive(repo_path, revs, env, hook_type='pre'))
handle_git_post_receive = (lambda repo_path, revs, env:
    handle_git_receive(repo_path, revs, env, hook_type='post'))


def handle_git_receive(repo_path, revs, env, hook_type='post'):
    """
    A really hacky method that is runned by git post-receive hook and logs
    an push action together with pushed revisions. It's executed by subprocess
    thus needs all info to be able to create a on the fly pylons enviroment,
    connect to database and run the logging code. Hacky as sh*t but works.

    :param repo_path:
    :param revs:
    :param env:
    """
    from paste.deploy import appconfig
    from sqlalchemy import engine_from_config
    from rhodecode.config.environment import load_environment
    from rhodecode.model import init_model
    from rhodecode.model.db import RhodeCodeUi
    from rhodecode.lib.utils import make_ui
    extras = _extract_extras(env)

    path, ini_name = os.path.split(extras['config'])
    conf = appconfig('config:%s' % ini_name, relative_to=path)
    load_environment(conf.global_conf, conf.local_conf)

    engine = engine_from_config(conf, 'sqlalchemy.db1.')
    init_model(engine)

    baseui = make_ui('db')
    # fix if it's not a bare repo
    if repo_path.endswith(os.sep + '.git'):
        repo_path = repo_path[:-5]

    repo = Repository.get_by_full_path(repo_path)
    if not repo:
        raise OSError('Repository %s not found in database'
                      % (safe_str(repo_path)))

    _hooks = dict(baseui.configitems('hooks')) or {}

    if hook_type == 'pre':
        repo = repo.scm_instance
    else:
        #post push shouldn't use the cached instance never
        repo = repo.scm_instance_no_cache()

    if hook_type == 'pre':
        pre_push(baseui, repo)

    # if push hook is enabled via web interface
    elif hook_type == 'post' and _hooks.get(RhodeCodeUi.HOOK_PUSH):

        rev_data = []
        for l in revs:
            old_rev, new_rev, ref = l.split(' ')
            _ref_data = ref.split('/')
            if _ref_data[1] in ['tags', 'heads']:
                rev_data.append({'old_rev': old_rev,
                                 'new_rev': new_rev,
                                 'ref': ref,
                                 'type': _ref_data[1],
                                 'name': _ref_data[2].strip()})

        git_revs = []
        for push_ref  in rev_data:
            _type = push_ref['type']
            if _type == 'heads':
                if push_ref['old_rev'] == EmptyChangeset().raw_id:
                    cmd = "for-each-ref --format='%(refname)' 'refs/heads/*'"
                    heads = repo.run_git_command(cmd)[0]
                    heads = heads.replace(push_ref['ref'], '')
                    heads = ' '.join(map(lambda c: c.strip('\n').strip(),
                                         heads.splitlines()))
                    cmd = (('log %(new_rev)s' % push_ref) +
                           ' --reverse --pretty=format:"%H" --not ' + heads)
                    git_revs += repo.run_git_command(cmd)[0].splitlines()

                elif push_ref['new_rev'] == EmptyChangeset().raw_id:
                    #delete branch case
                    git_revs += ['delete_branch=>%s' % push_ref['name']]
                else:
                    cmd = (('log %(old_rev)s..%(new_rev)s' % push_ref) +
                           ' --reverse --pretty=format:"%H"')
                    git_revs += repo.run_git_command(cmd)[0].splitlines()

            elif _type == 'tags':
                git_revs += ['tag=>%s' % push_ref['name']]

        log_push_action(baseui, repo, _git_revs=git_revs)
