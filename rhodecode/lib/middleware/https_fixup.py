# -*- coding: utf-8 -*-
"""
    rhodecode.lib.middleware.https_fixup
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    middleware to handle https correctly

    :created_on: May 23, 2010
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

from rhodecode.lib import str2bool


class HttpsFixup(object):

    def __init__(self, app, config):
        self.application = app
        self.config = config

    def __call__(self, environ, start_response):
        self.__fixup(environ)
        return self.application(environ, start_response)

    def __fixup(self, environ):
        """
        Function to fixup the environ as needed. In order to use this
        middleware you should set this header inside your
        proxy ie. nginx, apache etc.
        """
        proto = environ.get('HTTP_X_URL_SCHEME')

        if str2bool(self.config.get('force_https')):
            proto = 'https'

        if proto == 'https':
            environ['wsgi.url_scheme'] = proto
        else:
            environ['wsgi.url_scheme'] = 'http'
        return None
