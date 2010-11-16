import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('ldap')

#==============================================================================
# LDAP
#Name     = Just a description for the auth modes page
#Host     = DepartmentName.OrganizationName.local/ IP
#Port     = 389 default for ldap
#LDAPS    = no set True if You need to use ldaps
#Account  = DepartmentName\UserName (or UserName@MyDomain depending on AD server)
#Password = <password>
#Base DN  = DC=DepartmentName,DC=OrganizationName,DC=local
#
#On-the-fly user creation = yes
#Attributes
#  Login     = sAMAccountName
#  Firstname = givenName
#  Lastname  = sN
#  Email     = mail

#==============================================================================
class UsernameError(Exception):pass
class PasswordError(Exception):pass

LDAP_USE_LDAPS = False
ldap_server_type = 'ldap'
LDAP_SERVER_ADDRESS = 'myldap.com'
LDAP_SERVER_PORT = '389'

#USE FOR READ ONLY BIND TO LDAP SERVER
LDAP_BIND_DN = ''
LDAP_BIND_PASS = ''

if LDAP_USE_LDAPS:ldap_server_type = ldap_server_type + 's'
LDAP_SERVER = "%s://%s:%s" % (ldap_server_type,
                                       LDAP_SERVER_ADDRESS,
                                       LDAP_SERVER_PORT)

BASE_DN = "ou=people,dc=server,dc=com"
AUTH_DN = "uid=%s,%s"

def authenticate_ldap(username, password):
    """Authenticate a user via LDAP and return his/her LDAP properties.

    Raises AuthenticationError if the credentials are rejected, or
    EnvironmentError if the LDAP server can't be reached.
    """
    try:
        import ldap
    except ImportError:
        raise Exception('Could not import ldap make sure You install python-ldap')

    from rhodecode.lib.helpers import chop_at

    uid = chop_at(username, "@%s" % LDAP_SERVER_ADDRESS)
    dn = AUTH_DN % (uid, BASE_DN)
    log.debug("Authenticating %r at %s", dn, LDAP_SERVER)
    if "," in username:
        raise UsernameError("invalid character in username: ,")
    try:
        #ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, '/etc/openldap/cacerts')
        server = ldap.initialize(LDAP_SERVER)
        server.protocol = ldap.VERSION3
        
        if LDAP_BIND_DN and LDAP_BIND_PASS:
            server.simple_bind_s(AUTH_DN % (LDAP_BIND_DN,
                                            LDAP_BIND_PASS),
                                            password)
        
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
        raise EnvironmentError("can't access authentication server")
    return properties


print authenticate_ldap('test', 'test')
