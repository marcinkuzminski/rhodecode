# -*- coding: utf-8 -*-
"""
    rhodecode.lib.paster_commands.make_rcextensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    repo-scan paster command for RhodeCode


    :created_on: Feb 9, 2013
    :author: marcink
    :copyright: (C) 2010-2013 Marcin Kuzminski <marcin@python-works.com>
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

from rhodecode.model.scm import ScmModel
from rhodecode.lib.utils import BasePasterCommand, repo2db_mapper

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
    summary = "Rescan default location for new repositories"

    def command(self):
        #get SqlAlchemy session
        self._init_session()
        rm_obsolete = self.options.delete_obsolete
        log.info('Now scanning root location for new repos...')
        added, removed = repo2db_mapper(ScmModel().repo_scan(),
                                        remove_obsolete=rm_obsolete)
        added = ', '.join(added) or '-'
        removed = ', '.join(removed) or '-'
        log.info('Scan completed added: %s removed: %s' % (added, removed))

    def update_parser(self):
        self.parser.add_option(
            '--delete-obsolete',
            action='store_true',
            help="Use this flag do delete repositories that are "
                 "present in RhodeCode database but not on the filesystem",
        )
