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
import binascii
from inspect import isfunction

from mercurial.scmutil import revrange
from mercurial.node import nullrev

from rhodecode.lib import helpers as h
from rhodecode.lib.utils import action_logger
from rhodecode.lib.vcs.backends.base import EmptyChangeset


def _get_scm_size(alias, root_path):

    if not alias.startswith('.'):
        alias += '.'

    size_scm, size_root = 0, 0
    for path, dirs, files in os.walk(root_path):
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


def log_pull_action(ui, repo, **kwargs):
    """
    Logs user last pull action

    :param ui:
    :param repo:
    """

    extras = dict(repo.ui.configitems('rhodecode_extras'))
    username = extras['username']
    repository = extras['repository']
    scm = extras['scm']
    action = 'pull'

    action_logger(username, action, repository, extras['ip'], commit=True)
    # extension hook call
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'PULL_HOOK', None)

    if isfunction(callback):
        kw = {}
        kw.update(extras)
        callback(**kw)
    return 0


def log_push_action(ui, repo, **kwargs):
    """
    Maps user last push action to new changeset id, from mercurial

    :param ui:
    :param repo: repo object containing the `ui` object
    """

    extras = dict(repo.ui.configitems('rhodecode_extras'))
    username = extras['username']
    repository = extras['repository']
    action = extras['action'] + ':%s'
    scm = extras['scm']

    if scm == 'hg':
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
    elif scm == 'git':
        revs = kwargs.get('_git_revs', [])
        if '_git_revs' in kwargs:
            kwargs.pop('_git_revs')

    action = action % ','.join(revs)

    action_logger(username, action, repository, extras['ip'], commit=True)

    # extension hook call
    from rhodecode import EXTENSIONS
    callback = getattr(EXTENSIONS, 'PUSH_HOOK', None)
    if isfunction(callback):
        kw = {'pushed_revs': revs}
        kw.update(extras)
        callback(**kw)
    return 0


def log_create_repository(repository_dict, created_by, **kwargs):
    """
    Post create repository Hook. This is a dummy function for admins to re-use
    if needed. It's taken from rhodecode-extensions module and executed
    if present

    :param repository: dict dump of repository object
    :param created_by: username who created repository
    :param created_date: date of creation

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


def handle_git_post_receive(repo_path, revs, env):
    """
    A really hacky method that is runned by git post-receive hook and logs
    an push action together with pushed revisions. It's runned by subprocess
    thus needs all info to be able to create a temp pylons enviroment, connect
    to database and run the logging code. Hacky as sh**t but works. ps.
    GIT SUCKS

    :param repo_path:
    :type repo_path:
    :param revs:
    :type revs:
    :param env:
    :type env:
    """
    from paste.deploy import appconfig
    from sqlalchemy import engine_from_config
    from rhodecode.config.environment import load_environment
    from rhodecode.model import init_model
    from rhodecode.model.db import RhodeCodeUi
    from rhodecode.lib.utils import make_ui
    from rhodecode.model.db import Repository

    path, ini_name = os.path.split(env['RHODECODE_CONFIG_FILE'])
    conf = appconfig('config:%s' % ini_name, relative_to=path)
    load_environment(conf.global_conf, conf.local_conf)

    engine = engine_from_config(conf, 'sqlalchemy.db1.')
    init_model(engine)

    baseui = make_ui('db')
    repo = Repository.get_by_full_path(repo_path)

    _hooks = dict(baseui.configitems('hooks')) or {}
    # if push hook is enabled via web interface
    if _hooks.get(RhodeCodeUi.HOOK_PUSH):

        extras = {
         'username': env['RHODECODE_USER'],
         'repository': repo.repo_name,
         'scm': 'git',
         'action': 'push',
         'ip': env['RHODECODE_CONFIG_IP'],
        }
        for k, v in extras.items():
            baseui.setconfig('rhodecode_extras', k, v)
        repo = repo.scm_instance
        repo.ui = baseui
        old_rev, new_rev, ref = revs
        if old_rev == EmptyChangeset().raw_id:
            cmd = "for-each-ref --format='%(refname)' 'refs/heads/*'"
            heads = repo.run_git_command(cmd)[0]
            heads = heads.replace(ref, '')
            cmd = 'log ' + new_rev + ' --reverse --pretty=format:"%H" --not ' + heads
        else:
            cmd = 'log ' + old_rev + '..' + new_rev + ' --reverse --pretty=format:"%H"'
        git_revs = repo.run_git_command(cmd)[0].splitlines()

        log_push_action(baseui, repo, _git_revs=git_revs)
