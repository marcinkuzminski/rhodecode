# -*- coding: utf-8 -*-
"""
    rhodecode.lib.middleware.sentry
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    middleware to handle sentry/raven publishing of errors

    :created_on: September 18, 2012
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

try:
    from raven.base import Client
    from raven.contrib.pylons import list_from_setting
    from raven.middleware import Sentry as Middleware
except ImportError:
    Sentry = None
else:
    class Sentry(Middleware):
        def __init__(self, app, config, client_cls=Client):
            client = client_cls(
                dsn=config.get('sentry.dsn'),
                servers=list_from_setting(config, 'sentry.servers'),
                name=config.get('sentry.name'),
                key=config.get('sentry.key'),
                public_key=config.get('sentry.public_key'),
                secret_key=config.get('sentry.secret_key'),
                project=config.get('sentry.project'),
                site=config.get('sentry.site'),
                include_paths=list_from_setting(config, 'sentry.include_paths'),
                exclude_paths=list_from_setting(config, 'sentry.exclude_paths'),
            )
            super(Sentry, self).__init__(app, client)
