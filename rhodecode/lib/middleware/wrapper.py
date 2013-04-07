# -*- coding: utf-8 -*-
"""
    rhodecode.lib.middleware.wrapper
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    request time mesuring app

    :created_on: May 23, 2013
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
import time
import logging
from rhodecode.lib.base import _get_ip_addr, _get_access_path
from rhodecode.lib.utils2 import safe_unicode


class RequestWrapper(object):

    def __init__(self, app, config):
        self.application = app
        self.config = config

    def __call__(self, environ, start_response):
        start = time.time()
        try:
            return self.application(environ, start_response)
        finally:
            log = logging.getLogger('rhodecode.' + self.__class__.__name__)
            log.info('IP: %s Request to %s time: %.3fs' % (
                _get_ip_addr(environ),
                safe_unicode(_get_access_path(environ)), time.time() - start)
            )
