# -*- coding: utf-8 -*-
"""
    package.rhodecode.lib.cleanup
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
import re
import shutil
import logging
import datetime
import string

from os.path import dirname as dn, join as jn
from rhodecode.model import init_model
from rhodecode.lib.utils2 import engine_from_config, safe_str
from rhodecode.model.db import RhodeCodeUi, Repository
from rhodecode.lib.vcs.backends.base import EmptyChangeset


#to get the rhodecode import
sys.path.append(dn(dn(dn(os.path.realpath(__file__)))))

from rhodecode.lib.utils import BasePasterCommand, Command, add_cache

log = logging.getLogger(__name__)


class UpdateCommand(BasePasterCommand):

    max_args = 1
    min_args = 1

    usage = "CONFIG_FILE"
    summary = "Cleanup deleted repos"
    group_name = "RhodeCode"
    takes_config_file = -1
    parser = Command.standard_parser(verbose=True)

    def command(self):
        logging.config.fileConfig(self.path_to_ini_file)
        from pylons import config

        #get to remove repos !!
        add_cache(config)
        engine = engine_from_config(config, 'sqlalchemy.db1.')
        init_model(engine)

        repo_update_list = map(string.strip,
                               self.options.repo_update_list.split(',')) \
                               if self.options.repo_update_list else None

        if repo_update_list:
            repo_list = Repository.query().filter(Repository.repo_name.in_(repo_update_list))
        else:
            repo_list = Repository.getAll()
        for repo in repo_list:
            last_cs = (repo.scm_instance.get_changeset() if repo.scm_instance
                           else EmptyChangeset())
            repo.update_changeset_cache(last_cs)

    def update_parser(self):
        self.parser.add_option('--update-only',
                          action='store',
                          dest='repo_update_list',
                          help="Specifies a comma separated list of repositores "
                                "to update last commit info for. OPTIONAL",
                          )
