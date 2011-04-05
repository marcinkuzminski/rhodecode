# -*- coding: utf-8 -*-
"""
    rhodecode.lib.dbmigrate.__init__
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Database migration modules

    :created_on: Dec 11, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
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

import logging
from sqlalchemy import engine_from_config


from rhodecode.lib.utils import BasePasterCommand, Command, add_cache
from rhodecode.lib.db_manage import DbManage

log = logging.getLogger(__name__)


class UpgradeDb(BasePasterCommand):
    """Command used for paster to upgrade our database to newer version
    """

    max_args = 1
    min_args = 1

    usage = "CONFIG_FILE"
    summary = "Upgrades current db to newer version given configuration file"
    group_name = "RhodeCode"

    parser = Command.standard_parser(verbose=True)

    def command(self):
        from pylons import config

        add_cache(config)

        db_uri = config['sqlalchemy.db1.url']

        dbmanage = DbManage(log_sql=True, dbconf=db_uri,
                            root=config['here'], tests=False)

        dbmanage.upgrade()

    def update_parser(self):
        self.parser.add_option('--sql',
                      action='store_true',
                      dest='just_sql',
                      help="Prints upgrade sql for further investigation",
                      default=False)
