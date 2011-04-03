# -*- coding: utf-8 -*-
"""
    rhodecode.model.settings
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Settings model for RhodeCode

    :created on Nov 17, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

import logging

from rhodecode.model import BaseModel
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import  RhodeCodeSettings

log = logging.getLogger(__name__)

class SettingsModel(BaseModel):
    """
    Settings model
    """

    def get(self, settings_key, cache=False):
        r = self.sa.query(RhodeCodeSettings)\
            .filter(RhodeCodeSettings.app_settings_name == settings_key).scalar()
        if cache:
            r = r.options(FromCache("sql_cache_short",
                                          "get_setting_%s" % settings_key))
        return r

    def get_app_settings(self, cache=False):
        """Get's config from database, each config key is prefixed with
        'rhodecode_' prefix, than global pylons config is updated with such
        keys
        """

        ret = self.sa.query(RhodeCodeSettings)

        if cache:
            ret = ret.options(FromCache("sql_cache_short", "get_hg_settings"))

        if not ret:
            raise Exception('Could not get application settings !')
        settings = {}
        for each in ret:
            settings['rhodecode_' + each.app_settings_name] = each.app_settings_value

        return settings

    def get_ldap_settings(self):
        """
        Returns ldap settings from database
        :returns:
        ldap_active
        ldap_host
        ldap_port
        ldap_ldaps
        ldap_tls_reqcert
        ldap_dn_user
        ldap_dn_pass
        ldap_base_dn
        ldap_filter
        ldap_search_scope
        ldap_attr_login
        ldap_attr_firstname
        ldap_attr_lastname
        ldap_attr_email
        """
        # ldap_search_scope

        r = self.sa.query(RhodeCodeSettings)\
                .filter(RhodeCodeSettings.app_settings_name\
                        .startswith('ldap_'))\
                .all()

        fd = {}

        for row in r:
            v = row.app_settings_value
            if v in ['true', 'yes', 'on', 'y', 't', '1']:
                v = True
            elif v in ['false', 'no', 'off', 'n', 'f', '0']:
                v = False

            fd.update({row.app_settings_name:v})

        return fd
