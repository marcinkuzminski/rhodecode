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

from os.path import dirname as dn, join as jn
from rhodecode.model import init_model
from rhodecode.lib.utils2 import engine_from_config
from rhodecode.model.db import RhodeCodeUi


#to get the rhodecode import
sys.path.append(dn(dn(dn(os.path.realpath(__file__)))))

from rhodecode.lib.utils import BasePasterCommand, Command, ask_ok,\
    REMOVED_REPO_PAT, add_cache

log = logging.getLogger(__name__)


class CleanupCommand(BasePasterCommand):

    max_args = 1
    min_args = 1

    usage = "CONFIG_FILE"
    summary = "Cleanup deleted repos"
    group_name = "RhodeCode"
    takes_config_file = -1
    parser = Command.standard_parser(verbose=True)

    def _parse_older_than(self, val):
        regex = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
        parts = regex.match(val)
        if not parts:
            return
        parts = parts.groupdict()
        time_params = {}
        for (name, param) in parts.iteritems():
            if param:
                time_params[name] = int(param)
        return datetime.timedelta(**time_params)

    def _extract_date(self, name):
        """
        Extract the date part from rm__<date> pattern of removed repos,
        and convert it to datetime object

        :param name:
        """
        date_part = name[4:19]  # 4:19 since we don't parse milisecods
        return datetime.datetime.strptime(date_part, '%Y%m%d_%H%M%S')

    def command(self):
        logging.config.fileConfig(self.path_to_ini_file)
        from pylons import config

        #get to remove repos !!
        add_cache(config)
        engine = engine_from_config(config, 'sqlalchemy.db1.')
        init_model(engine)

        repos_location = RhodeCodeUi.get_repos_location()
        to_remove = []
        for loc in os.listdir(repos_location):
            if REMOVED_REPO_PAT.match(loc):
                to_remove.append([loc, self._extract_date(loc)])

        #filter older than (if present)!
        now = datetime.datetime.now()
        older_than = self.options.older_than
        if older_than:
            to_remove_filtered = []
            older_than_date = self._parse_older_than(older_than)
            for name, date_ in to_remove:
                repo_age = now - date_
                if repo_age > older_than_date:
                    to_remove_filtered.append([name, date_])

            to_remove = to_remove_filtered
            print >> sys.stdout, 'removing [%s] deleted repos older than %s[%s]' \
                % (len(to_remove), older_than, older_than_date)
        else:
            print >> sys.stdout, 'removing all [%s] deleted repos' \
                % len(to_remove)
        if self.options.dont_ask or not to_remove:
            # don't ask just remove !
            remove = True
        else:
            remove = ask_ok('are you sure to remove listed repos \n%s [y/n]?'
                            % ', \n'.join(['%s removed on %s' % (x[0], x[1])
                                           for x in to_remove]))

        if remove:
            for name, date_ in to_remove:
                print >> sys.stdout, 'removing repository %s' % name
                shutil.rmtree(os.path.join(repos_location, name))
        else:
            print 'nothing done exiting...'
            sys.exit(0)

    def update_parser(self):
        self.parser.add_option('--older-than',
                          action='store',
                          dest='older_than',
                          help=(
                            "only remove repos that have been removed "
                            "at least given time ago "
                            "ex. --older-than=30d deletes repositores "
                            "removed more than 30days ago. Possible options "
                            "d[ays]/h[ours]/m[inutes]/s[seconds]. OPTIONAL"),
                          )
        self.parser.add_option('--dont-ask',
                               action='store_true',
                               dest='dont_ask',
                               help=("Don't ask to remove repos"))
