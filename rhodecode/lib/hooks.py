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

from mercurial.scmutil import revrange
from mercurial.node import nullrev

from rhodecode.lib import helpers as h
from rhodecode.lib.utils import action_logger


def repo_size(ui, repo, hooktype=None, **kwargs):
    """
    Presents size of repository after push

    :param ui:
    :param repo:
    :param hooktype:
    """

    size_hg, size_root = 0, 0
    for path, dirs, files in os.walk(repo.root):
        if path.find('.hg') != -1:
            for f in files:
                try:
                    size_hg += os.path.getsize(os.path.join(path, f))
                except OSError:
                    pass
        else:
            for f in files:
                try:
                    size_root += os.path.getsize(os.path.join(path, f))
                except OSError:
                    pass

    size_hg_f = h.format_byte_size(size_hg)
    size_root_f = h.format_byte_size(size_root)
    size_total_f = h.format_byte_size(size_root + size_hg)

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

    extra_params = dict(repo.ui.configitems('rhodecode_extras'))
    username = extra_params['username']
    repository = extra_params['repository']
    action = 'pull'

    action_logger(username, action, repository, extra_params['ip'],
                  commit=True)

    return 0


def log_push_action(ui, repo, **kwargs):
    """
    Maps user last push action to new changeset id, from mercurial

    :param ui:
    :param repo:
    """

    extra_params = dict(repo.ui.configitems('rhodecode_extras'))
    username = extra_params['username']
    repository = extra_params['repository']
    action = extra_params['action'] + ':%s'
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

    revs = (str(repo[r]) for r in xrange(start, stop + 1))

    action = action % ','.join(revs)

    action_logger(username, action, repository, extra_params['ip'],
                  commit=True)

    return 0


def log_create_repository(repository_dict, created_by, **kwargs):
    """
    Post create repository Hook. This is a dummy function for admins to re-use
    if needed

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


    return 0
