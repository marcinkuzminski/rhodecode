# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.changelog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    RhodeCode authentication library for LDAP

    :created_on: Created on Nov 17, 2010
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

import logging

from rhodecode.lib.exceptions import LdapConnectionError, LdapUsernameError, \
    LdapPasswordError

log = logging.getLogger(__name__)


try:
    import ldap
except ImportError:
    # means that python-ldap is not installed
    pass


class AuthLdap(object):

    def __init__(self, server, base_dn, port=389, bind_dn='', bind_pass='',
                 tls_kind='PLAIN', tls_reqcert='DEMAND', ldap_version=3,
                 ldap_filter='(&(objectClass=user)(!(objectClass=computer)))',
                 search_scope='SUBTREE', attr_login='uid'):
        self.ldap_version = ldap_version
        ldap_server_type = 'ldap'

        self.TLS_KIND = tls_kind

        if self.TLS_KIND == 'LDAPS':
            port = port or 689
            ldap_server_type = ldap_server_type + 's'

        OPT_X_TLS_DEMAND = 2
        self.TLS_REQCERT = getattr(ldap, 'OPT_X_TLS_%s' % tls_reqcert,
                                   OPT_X_TLS_DEMAND)
        self.LDAP_SERVER_ADDRESS = server
        self.LDAP_SERVER_PORT = port

        # USE FOR READ ONLY BIND TO LDAP SERVER
        self.LDAP_BIND_DN = bind_dn
        self.LDAP_BIND_PASS = bind_pass

        self.LDAP_SERVER = "%s://%s:%s" % (ldap_server_type,
                                           self.LDAP_SERVER_ADDRESS,
                                           self.LDAP_SERVER_PORT)

        self.BASE_DN = base_dn
        self.LDAP_FILTER = ldap_filter
        self.SEARCH_SCOPE = getattr(ldap, 'SCOPE_%s' % search_scope)
        self.attr_login = attr_login

    def authenticate_ldap(self, username, password):
        """
        Authenticate a user via LDAP and return his/her LDAP properties.

        Raises AuthenticationError if the credentials are rejected, or
        EnvironmentError if the LDAP server can't be reached.

        :param username: username
        :param password: password
        """

        from rhodecode.lib.helpers import chop_at

        uid = chop_at(username, "@%s" % self.LDAP_SERVER_ADDRESS)

        if not password:
            log.debug("Attempt to authenticate LDAP user "
                      "with blank password rejected.")
            raise LdapPasswordError()
        if "," in username:
            raise LdapUsernameError("invalid character in username: ,")
        try:
            if hasattr(ldap, 'OPT_X_TLS_CACERTDIR'):
                ldap.set_option(ldap.OPT_X_TLS_CACERTDIR,
                                '/etc/openldap/cacerts')
            ldap.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)
            ldap.set_option(ldap.OPT_RESTART, ldap.OPT_ON)
            ldap.set_option(ldap.OPT_TIMEOUT, 20)
            ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
            ldap.set_option(ldap.OPT_TIMELIMIT, 15)
            if self.TLS_KIND != 'PLAIN':
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, self.TLS_REQCERT)
            server = ldap.initialize(self.LDAP_SERVER)
            if self.ldap_version == 2:
                server.protocol = ldap.VERSION2
            else:
                server.protocol = ldap.VERSION3

            if self.TLS_KIND == 'START_TLS':
                server.start_tls_s()

            if self.LDAP_BIND_DN and self.LDAP_BIND_PASS:
                server.simple_bind_s(self.LDAP_BIND_DN, self.LDAP_BIND_PASS)

            filter_ = '(&%s(%s=%s))' % (self.LDAP_FILTER, self.attr_login,
                                     username)
            log.debug("Authenticating %r filter %s at %s", self.BASE_DN,
                      filter_, self.LDAP_SERVER)
            lobjects = server.search_ext_s(self.BASE_DN, self.SEARCH_SCOPE,
                                           filter_)

            if not lobjects:
                raise ldap.NO_SUCH_OBJECT()

            for (dn, _attrs) in lobjects:
                if dn is None:
                    continue

                try:
                    log.debug('Trying simple bind with %s' % dn)
                    server.simple_bind_s(dn, password)
                    attrs = server.search_ext_s(dn, ldap.SCOPE_BASE,
                                                '(objectClass=*)')[0][1]
                    break

                except ldap.INVALID_CREDENTIALS:
                    log.debug(
                        "LDAP rejected password for user '%s' (%s): %s" % (
                            uid, username, dn
                        )
                    )

            else:
                log.debug("No matching LDAP objects for authentication "
                          "of '%s' (%s)", uid, username)
                raise LdapPasswordError()

        except ldap.NO_SUCH_OBJECT:
            log.debug("LDAP says no such user '%s' (%s)" % (uid, username))
            raise LdapUsernameError()
        except ldap.SERVER_DOWN:
            raise LdapConnectionError("LDAP can't access "
                                      "authentication server")

        return (dn, attrs)
