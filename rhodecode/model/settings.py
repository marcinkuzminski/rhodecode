#!/usr/bin/env python
# encoding: utf-8
# Model for RhodeCode settings
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
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
"""
Created on Nov 17, 2010
Model for RhodeCode
@author: marcink
"""
from rhodecode.lib import helpers as h
from rhodecode.model import meta
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import  RhodeCodeSettings
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.session import make_transient
import logging

log = logging.getLogger(__name__)

class SettingsModel(object):
    """
    Settings model
    """

    def __init__(self):
        self.sa = meta.Session()


    def get(self, settings_key, cache=False):
        r = self.sa.query(RhodeCodeSettings)\
            .filter(RhodeCodeSettings.app_settings_name == settings_key).scalar()
        if cache:
            r = r.options(FromCache("sql_cache_short",
                                          "get_setting_%s" % settings_key))
        return r


    def get_ldap_settings(self):
        """
        Returns ldap settings from database
        :returns:
        ldap_active
        ldap_host
        ldap_port 
        ldap_ldaps
        ldap_dn_user 
        ldap_dn_pass 
        ldap_base_dn
        """

        r = self.sa.query(RhodeCodeSettings)\
                .filter(RhodeCodeSettings.app_settings_name\
                        .startswith('ldap_'))\
                .all()

        fd = {}

        for row in r:
            v = row.app_settings_value
            if v in ['0', '1']:
                v = v == '1'
            fd.update({row.app_settings_name:v})

        return fd
