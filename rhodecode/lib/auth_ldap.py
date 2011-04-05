#!/usr/bin/env python
# encoding: utf-8
# ldap authentication lib
# Copyright (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
#
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
"""
Created on Nov 17, 2010

@author: marcink
"""

from rhodecode.lib.exceptions import *
import logging

log = logging.getLogger(__name__)

try:
    import ldap
except ImportError:
    pass

class AuthLdap(object):

    def __init__(self, server, base_dn, port=389, bind_dn='', bind_pass='',
                 use_ldaps=False, ldap_version=3):
        self.ldap_version = ldap_version
        if use_ldaps:
            port = port or 689
        self.LDAP_USE_LDAPS = use_ldaps
        self.LDAP_SERVER_ADDRESS = server
        self.LDAP_SERVER_PORT = port

        #USE FOR READ ONLY BIND TO LDAP SERVER
        self.LDAP_BIND_DN = bind_dn
        self.LDAP_BIND_PASS = bind_pass

        ldap_server_type = 'ldap'
        if self.LDAP_USE_LDAPS:ldap_server_type = ldap_server_type + 's'
        self.LDAP_SERVER = "%s://%s:%s" % (ldap_server_type,
                                               self.LDAP_SERVER_ADDRESS,
                                               self.LDAP_SERVER_PORT)

        self.BASE_DN = base_dn

    def authenticate_ldap(self, username, password):
        """Authenticate a user via LDAP and return his/her LDAP properties.
    
        Raises AuthenticationError if the credentials are rejected, or
        EnvironmentError if the LDAP server can't be reached.
        
        :param username: username
        :param password: password
        """

        from rhodecode.lib.helpers import chop_at

        uid = chop_at(username, "@%s" % self.LDAP_SERVER_ADDRESS)

        if "," in username:
            raise LdapUsernameError("invalid character in username: ,")
        try:
            ldap.set_option(ldap.OPT_X_TLS_CACERTDIR, '/etc/openldap/cacerts')
            ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
            server = ldap.initialize(self.LDAP_SERVER)
            if self.ldap_version == 2:
                server.protocol = ldap.VERSION2
            else:
                server.protocol = ldap.VERSION3

            if self.LDAP_BIND_DN and self.LDAP_BIND_PASS:
                server.simple_bind_s(self.LDAP_BIND_DN, self.LDAP_BIND_PASS)

            dn = self.BASE_DN % {'user':uid}
            log.debug("Authenticating %r at %s", dn, self.LDAP_SERVER)
            server.simple_bind_s(dn, password)

            properties = server.search_s(dn, ldap.SCOPE_SUBTREE)
            if not properties:
                raise ldap.NO_SUCH_OBJECT()
        except ldap.NO_SUCH_OBJECT, e:
            log.debug("LDAP says no such user '%s' (%s)", uid, username)
            raise LdapUsernameError()
        except ldap.INVALID_CREDENTIALS, e:
            log.debug("LDAP rejected password for user '%s' (%s)", uid, username)
            raise LdapPasswordError()
        except ldap.SERVER_DOWN, e:
            raise LdapConnectionError("LDAP can't access authentication server")

        return properties[0]

