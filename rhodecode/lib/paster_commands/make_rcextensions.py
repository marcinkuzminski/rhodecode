# -*- coding: utf-8 -*-
"""
    rhodecode.lib.paster_commands.make_rcextensions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    make-rcext paster command for RhodeCode

    :created_on: Mar 6, 2012
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
import pkg_resources

from rhodecode.lib.utils import BasePasterCommand, ask_ok

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
    summary = "Creates additional extensions for rhodecode"

    def command(self):
        logging.config.fileConfig(self.path_to_ini_file)
        from pylons import config

        def _make_file(ext_file, tmpl):
            bdir = os.path.split(ext_file)[0]
            if not os.path.isdir(bdir):
                os.makedirs(bdir)
            with open(ext_file, 'wb') as f:
                f.write(tmpl)
                log.info('Writen new extensions file to %s' % ext_file)

        here = config['here']
        tmpl = pkg_resources.resource_string(
            'rhodecode', os.path.join('config', 'rcextensions', '__init__.py')
        )
        ext_file = os.path.join(here, 'rcextensions', '__init__.py')
        if os.path.exists(ext_file):
            msg = ('Extension file already exists, do you want '
                   'to overwrite it ? [y/n]')
            if ask_ok(msg):
                _make_file(ext_file, tmpl)
            else:
                log.info('nothing done...')
        else:
            _make_file(ext_file, tmpl)

    def update_parser(self):
        pass
