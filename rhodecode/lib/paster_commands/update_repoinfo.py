# -*- coding: utf-8 -*-
"""
    rhodecode.lib.paster_commands.make_rcextensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    uodate-repoinfo paster command for RhodeCode

    :created_on: Jul 14, 2012
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
import sys
import logging
import string

from rhodecode.lib.utils import BasePasterCommand
from rhodecode.model.db import Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.meta import Session

# fix rhodecode import
from os.path import dirname as dn
rc_path = dn(dn(dn(os.path.realpath(__file__))))
sys.path.append(rc_path)

log = logging.getLogger(__name__)


class Command(BasePasterCommand):

    max_args = 1
    min_args = 1

    usage = "CONFIG_FILE"
    group_name = "RhodeCode"
    takes_config_file = -1
    parser = BasePasterCommand.standard_parser(verbose=True)
    summary = "Updates repositories caches for last changeset"

    def command(self):
        #get SqlAlchemy session
        self._init_session()

        repo_update_list = map(string.strip,
                               self.options.repo_update_list.split(',')) \
                               if self.options.repo_update_list else None

        if repo_update_list:
            repo_list = Repository.query()\
                .filter(Repository.repo_name.in_(repo_update_list))
        else:
            repo_list = Repository.getAll()
        RepoModel.update_repoinfo(repositories=repo_list)
        Session().commit()

        if self.options.invalidate_cache:
            for r in repo_list:
                r.set_invalidate()
        log.info('Updated cache for %s repositories' % (len(repo_list)))

    def update_parser(self):
        self.parser.add_option('--update-only',
                           action='store',
                           dest='repo_update_list',
                           help="Specifies a comma separated list of repositores "
                                "to update last commit info for. OPTIONAL")
        self.parser.add_option('--invalidate-cache',
                           action='store_true',
                           dest='invalidate_cache',
                           help="Trigger cache invalidation event for repos. "
                                "OPTIONAL")
