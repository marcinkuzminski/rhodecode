#==============================================================================
# LDAP
#Name     = Just a description for the auth modes page
#Host     = DepartmentName.OrganizationName.local/ IP
#Port     = 389 default for ldap
#LDAPS    = no set True if You need to use ldaps
#Account  = DepartmentName\UserName (or UserName@MyDomain depending on AD server)
#Password = <password>
#Base DN  = DC=DepartmentName,DC=OrganizationName,DC=local

#==============================================================================

from rhodecode.lib.exceptions import LdapImportError, UsernameError, \
    PasswordError, ConnectionError
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
        self.AUTH_DN = "uid=%s,%s"

    def authenticate_ldap(self, username, password):
        """Authenticate a user via LDAP and return his/her LDAP properties.
    
        Raises AuthenticationError if the credentials are rejected, or
        EnvironmentError if the LDAP server can't be reached.
        
        :param username: username
        :param password: password
        """

        from rhodecode.lib.helpers import chop_at

        uid = chop_at(username, "@%s" % self.LDAP_SERVER_ADDRESS)
        dn = self.AUTH_DN % (uid, self.BASE_DN)
        log.debug("Authenticating %r at %s", dn, self.LDAP_SERVER)
        if "," in username:
            raise UsernameError("invalid character in username: ,")
        try:
            ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, '/etc/openldap/cacerts')
            ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
            server = ldap.initialize(self.LDAP_SERVER)
            if self.ldap_version == 2:
                server.protocol = ldap.VERSION2
            else:
                server.protocol = ldap.VERSION3

            if self.LDAP_BIND_DN and self.LDAP_BIND_PASS:
                server.simple_bind_s(self.AUTH_DN % (self.LDAP_BIND_DN,
                                                self.BASE_DN),
                                                self.LDAP_BIND_PASS)

            server.simple_bind_s(dn, password)
            properties = server.search_s(dn, ldap.SCOPE_SUBTREE)
            if not properties:
                raise ldap.NO_SUCH_OBJECT()
        except ldap.NO_SUCH_OBJECT, e:
            log.debug("LDAP says no such user '%s' (%s)", uid, username)
            raise UsernameError()
        except ldap.INVALID_CREDENTIALS, e:
            log.debug("LDAP rejected password for user '%s' (%s)", uid, username)
            raise PasswordError()
        except ldap.SERVER_DOWN, e:
            raise ConnectionError("LDAP can't access authentication server")

        return properties[0]

