# -*- coding: utf-8 -*-
"""
    rhodecode.lib.auth
    ~~~~~~~~~~~~~~~~~~

    authentication and permission libraries

    :created_on: Apr 4, 2010
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
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

import random
import logging
import traceback
import hashlib

from tempfile import _RandomNameSequence
from decorator import decorator

from pylons import config, session, url, request
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode import __platform__, PLATFORM_WIN, PLATFORM_OTHERS

if __platform__ in PLATFORM_WIN:
    from hashlib import sha256
if __platform__ in PLATFORM_OTHERS:
    import bcrypt

from rhodecode.lib import str2bool, safe_unicode
from rhodecode.lib.exceptions import LdapPasswordError, LdapUsernameError
from rhodecode.lib.utils import get_repo_slug
from rhodecode.lib.auth_ldap import AuthLdap

from rhodecode.model import meta
from rhodecode.model.user import UserModel
from rhodecode.model.db import Permission, RhodeCodeSettings, User

log = logging.getLogger(__name__)


class PasswordGenerator(object):
    """This is a simple class for generating password from
        different sets of characters
        usage:
        passwd_gen = PasswordGenerator()
        #print 8-letter password containing only big and small letters
            of alphabet
        print passwd_gen.gen_password(8, passwd_gen.ALPHABETS_BIG_SMALL)
    """
    ALPHABETS_NUM = r'''1234567890'''
    ALPHABETS_SMALL = r'''qwertyuiopasdfghjklzxcvbnm'''
    ALPHABETS_BIG = r'''QWERTYUIOPASDFGHJKLZXCVBNM'''
    ALPHABETS_SPECIAL = r'''`-=[]\;',./~!@#$%^&*()_+{}|:"<>?'''
    ALPHABETS_FULL = ALPHABETS_BIG + ALPHABETS_SMALL \
        + ALPHABETS_NUM + ALPHABETS_SPECIAL
    ALPHABETS_ALPHANUM = ALPHABETS_BIG + ALPHABETS_SMALL + ALPHABETS_NUM
    ALPHABETS_BIG_SMALL = ALPHABETS_BIG + ALPHABETS_SMALL
    ALPHABETS_ALPHANUM_BIG = ALPHABETS_BIG + ALPHABETS_NUM
    ALPHABETS_ALPHANUM_SMALL = ALPHABETS_SMALL + ALPHABETS_NUM

    def __init__(self, passwd=''):
        self.passwd = passwd

    def gen_password(self, len, type):
        self.passwd = ''.join([random.choice(type) for _ in xrange(len)])
        return self.passwd


class RhodeCodeCrypto(object):

    @classmethod
    def hash_string(cls, str_):
        """
        Cryptographic function used for password hashing based on pybcrypt
        or pycrypto in windows

        :param password: password to hash
        """
        if __platform__ in PLATFORM_WIN:
            return sha256(str_).hexdigest()
        elif __platform__ in PLATFORM_OTHERS:
            return bcrypt.hashpw(str_, bcrypt.gensalt(10))
        else:
            raise Exception('Unknown or unsupported platform %s' \
                            % __platform__)

    @classmethod
    def hash_check(cls, password, hashed):
        """
        Checks matching password with it's hashed value, runs different
        implementation based on platform it runs on

        :param password: password
        :param hashed: password in hashed form
        """

        if __platform__ in PLATFORM_WIN:
            return sha256(password).hexdigest() == hashed
        elif __platform__ in PLATFORM_OTHERS:
            return bcrypt.hashpw(password, hashed) == hashed
        else:
            raise Exception('Unknown or unsupported platform %s' \
                            % __platform__)


def get_crypt_password(password):
    return RhodeCodeCrypto.hash_string(password)


def check_password(password, hashed):
    return RhodeCodeCrypto.hash_check(password, hashed)


def generate_api_key(username, salt=None):
    if salt is None:
        salt = _RandomNameSequence().next()

    return hashlib.sha1(username + salt).hexdigest()


def authfunc(environ, username, password):
    """Dummy authentication function used in Mercurial/Git/ and access control,

    :param environ: needed only for using in Basic auth
    """
    return authenticate(username, password)


def authenticate(username, password):
    """Authentication function used for access control,
    firstly checks for db authentication then if ldap is enabled for ldap
    authentication, also creates ldap user if not in database

    :param username: username
    :param password: password
    """

    user_model = UserModel()
    user = User.get_by_username(username)

    log.debug('Authenticating user using RhodeCode account')
    if user is not None and not user.ldap_dn:
        if user.active:
            if user.username == 'default' and user.active:
                log.info('user %s authenticated correctly as anonymous user',
                         username)
                return True

            elif user.username == username and check_password(password,
                                                              user.password):
                log.info('user %s authenticated correctly', username)
                return True
        else:
            log.warning('user %s is disabled', username)

    else:
        log.debug('Regular authentication failed')
        user_obj = User.get_by_username(username, case_insensitive=True)

        if user_obj is not None and not user_obj.ldap_dn:
            log.debug('this user already exists as non ldap')
            return False

        ldap_settings = RhodeCodeSettings.get_ldap_settings()
        #======================================================================
        # FALLBACK TO LDAP AUTH IF ENABLE
        #======================================================================
        if str2bool(ldap_settings.get('ldap_active')):
            log.debug("Authenticating user using ldap")
            kwargs = {
                  'server': ldap_settings.get('ldap_host', ''),
                  'base_dn': ldap_settings.get('ldap_base_dn', ''),
                  'port': ldap_settings.get('ldap_port'),
                  'bind_dn': ldap_settings.get('ldap_dn_user'),
                  'bind_pass': ldap_settings.get('ldap_dn_pass'),
                  'tls_kind': ldap_settings.get('ldap_tls_kind'),
                  'tls_reqcert': ldap_settings.get('ldap_tls_reqcert'),
                  'ldap_filter': ldap_settings.get('ldap_filter'),
                  'search_scope': ldap_settings.get('ldap_search_scope'),
                  'attr_login': ldap_settings.get('ldap_attr_login'),
                  'ldap_version': 3,
                  }
            log.debug('Checking for ldap authentication')
            try:
                aldap = AuthLdap(**kwargs)
                (user_dn, ldap_attrs) = aldap.authenticate_ldap(username,
                                                                password)
                log.debug('Got ldap DN response %s', user_dn)

                get_ldap_attr = lambda k: ldap_attrs.get(ldap_settings\
                                                           .get(k), [''])[0]

                user_attrs = {
                 'name': safe_unicode(get_ldap_attr('ldap_attr_firstname')),
                 'lastname': safe_unicode(get_ldap_attr('ldap_attr_lastname')),
                 'email': get_ldap_attr('ldap_attr_email'),
                }

                if user_model.create_ldap(username, password, user_dn,
                                          user_attrs):
                    log.info('created new ldap user %s', username)

                return True
            except (LdapUsernameError, LdapPasswordError,):
                pass
            except (Exception,):
                log.error(traceback.format_exc())
                pass
    return False


class  AuthUser(object):
    """
    A simple object that handles all attributes of user in RhodeCode

    It does lookup based on API key,given user, or user present in session
    Then it fills all required information for such user. It also checks if
    anonymous access is enabled and if so, it returns default user as logged
    in
    """

    def __init__(self, user_id=None, api_key=None):

        self.user_id = user_id
        self.api_key = None

        self.username = 'None'
        self.name = ''
        self.lastname = ''
        self.email = ''
        self.is_authenticated = False
        self.admin = False
        self.permissions = {}
        self._api_key = api_key
        self.propagate_data()

    def propagate_data(self):
        user_model = UserModel()
        self.anonymous_user = User.get_by_username('default')
        if self._api_key and self._api_key != self.anonymous_user.api_key:
            #try go get user by api key
            log.debug('Auth User lookup by API KEY %s', self._api_key)
            user_model.fill_data(self, api_key=self._api_key)
        else:
            log.debug('Auth User lookup by USER ID %s', self.user_id)
            if self.user_id is not None \
                and self.user_id != self.anonymous_user.user_id:
                user_model.fill_data(self, user_id=self.user_id)
            else:
                if self.anonymous_user.active is True:
                    user_model.fill_data(self,
                                         user_id=self.anonymous_user.user_id)
                    #then we set this user is logged in
                    self.is_authenticated = True
                else:
                    self.is_authenticated = False

        log.debug('Auth User is now %s', self)
        user_model.fill_perms(self)

    @property
    def is_admin(self):
        return self.admin

    @property
    def full_contact(self):
        return '%s %s <%s>' % (self.name, self.lastname, self.email)

    def __repr__(self):
        return "<AuthUser('id:%s:%s|%s')>" % (self.user_id, self.username,
                                              self.is_authenticated)

    def set_authenticated(self, authenticated=True):

        if self.user_id != self.anonymous_user.user_id:
            self.is_authenticated = authenticated


def set_available_permissions(config):
    """This function will propagate pylons globals with all available defined
    permission given in db. We don't want to check each time from db for new
    permissions since adding a new permission also requires application restart
    ie. to decorate new views with the newly created permission

    :param config: current pylons config instance

    """
    log.info('getting information about all available permissions')
    try:
        sa = meta.Session()
        all_perms = sa.query(Permission).all()
    except:
        pass
    finally:
        meta.Session.remove()

    config['available_permissions'] = [x.permission_name for x in all_perms]


#==============================================================================
# CHECK DECORATORS
#==============================================================================
class LoginRequired(object):
    """
    Must be logged in to execute this function else
    redirect to login page

    :param api_access: if enabled this checks only for valid auth token
        and grants access based on valid token
    """

    def __init__(self, api_access=False):
        self.api_access = api_access

    def __call__(self, func):
        return decorator(self.__wrapper, func)

    def __wrapper(self, func, *fargs, **fkwargs):
        cls = fargs[0]
        user = cls.rhodecode_user

        api_access_ok = False
        if self.api_access:
            log.debug('Checking API KEY access for %s', cls)
            if user.api_key == request.GET.get('api_key'):
                api_access_ok = True
            else:
                log.debug("API KEY token not valid")

        log.debug('Checking if %s is authenticated @ %s', user.username, cls)
        if user.is_authenticated or api_access_ok:
            log.debug('user %s is authenticated', user.username)
            return func(*fargs, **fkwargs)
        else:
            log.warn('user %s NOT authenticated', user.username)
            p = url.current()

            log.debug('redirecting to login page with %s', p)
            return redirect(url('login_home', came_from=p))


class NotAnonymous(object):
    """Must be logged in to execute this function else
    redirect to login page"""

    def __call__(self, func):
        return decorator(self.__wrapper, func)

    def __wrapper(self, func, *fargs, **fkwargs):
        cls = fargs[0]
        self.user = cls.rhodecode_user

        log.debug('Checking if user is not anonymous @%s', cls)

        anonymous = self.user.username == 'default'

        if anonymous:
            p = url.current()

            import rhodecode.lib.helpers as h
            h.flash(_('You need to be a registered user to '
                      'perform this action'),
                    category='warning')
            return redirect(url('login_home', came_from=p))
        else:
            return func(*fargs, **fkwargs)


class PermsDecorator(object):
    """Base class for controller decorators"""

    def __init__(self, *required_perms):
        available_perms = config['available_permissions']
        for perm in required_perms:
            if perm not in available_perms:
                raise Exception("'%s' permission is not defined" % perm)
        self.required_perms = set(required_perms)
        self.user_perms = None

    def __call__(self, func):
        return decorator(self.__wrapper, func)

    def __wrapper(self, func, *fargs, **fkwargs):
        cls = fargs[0]
        self.user = cls.rhodecode_user
        self.user_perms = self.user.permissions
        log.debug('checking %s permissions %s for %s %s',
           self.__class__.__name__, self.required_perms, cls,
               self.user)

        if self.check_permissions():
            log.debug('Permission granted for %s %s', cls, self.user)
            return func(*fargs, **fkwargs)

        else:
            log.warning('Permission denied for %s %s', cls, self.user)


            anonymous = self.user.username == 'default'

            if anonymous:
                p = url.current()

                import rhodecode.lib.helpers as h
                h.flash(_('You need to be a signed in to '
                          'view this page'),
                        category='warning')
                return redirect(url('login_home', came_from=p))

            else:
                #redirect with forbidden ret code
                return abort(403)

    def check_permissions(self):
        """Dummy function for overriding"""
        raise Exception('You have to write this function in child class')


class HasPermissionAllDecorator(PermsDecorator):
    """Checks for access permission for all given predicates. All of them
    have to be meet in order to fulfill the request
    """

    def check_permissions(self):
        if self.required_perms.issubset(self.user_perms.get('global')):
            return True
        return False


class HasPermissionAnyDecorator(PermsDecorator):
    """Checks for access permission for any of given predicates. In order to
    fulfill the request any of predicates must be meet
    """

    def check_permissions(self):
        if self.required_perms.intersection(self.user_perms.get('global')):
            return True
        return False


class HasRepoPermissionAllDecorator(PermsDecorator):
    """Checks for access permission for all given predicates for specific
    repository. All of them have to be meet in order to fulfill the request
    """

    def check_permissions(self):
        repo_name = get_repo_slug(request)
        try:
            user_perms = set([self.user_perms['repositories'][repo_name]])
        except KeyError:
            return False
        if self.required_perms.issubset(user_perms):
            return True
        return False


class HasRepoPermissionAnyDecorator(PermsDecorator):
    """Checks for access permission for any of given predicates for specific
    repository. In order to fulfill the request any of predicates must be meet
    """

    def check_permissions(self):
        repo_name = get_repo_slug(request)

        try:
            user_perms = set([self.user_perms['repositories'][repo_name]])
        except KeyError:
            return False
        if self.required_perms.intersection(user_perms):
            return True
        return False


#==============================================================================
# CHECK FUNCTIONS
#==============================================================================
class PermsFunction(object):
    """Base function for other check functions"""

    def __init__(self, *perms):
        available_perms = config['available_permissions']

        for perm in perms:
            if perm not in available_perms:
                raise Exception("'%s' permission in not defined" % perm)
        self.required_perms = set(perms)
        self.user_perms = None
        self.granted_for = ''
        self.repo_name = None

    def __call__(self, check_Location=''):
        user = session.get('rhodecode_user', False)
        if not user:
            return False
        self.user_perms = user.permissions
        self.granted_for = user
        log.debug('checking %s %s %s', self.__class__.__name__,
                  self.required_perms, user)

        if self.check_permissions():
            log.debug('Permission granted %s @ %s', self.granted_for,
                      check_Location or 'unspecified location')
            return True

        else:
            log.warning('Permission denied for %s @ %s', self.granted_for,
                        check_Location or 'unspecified location')
            return False

    def check_permissions(self):
        """Dummy function for overriding"""
        raise Exception('You have to write this function in child class')


class HasPermissionAll(PermsFunction):
    def check_permissions(self):
        if self.required_perms.issubset(self.user_perms.get('global')):
            return True
        return False


class HasPermissionAny(PermsFunction):
    def check_permissions(self):
        if self.required_perms.intersection(self.user_perms.get('global')):
            return True
        return False


class HasRepoPermissionAll(PermsFunction):

    def __call__(self, repo_name=None, check_Location=''):
        self.repo_name = repo_name
        return super(HasRepoPermissionAll, self).__call__(check_Location)

    def check_permissions(self):
        if not self.repo_name:
            self.repo_name = get_repo_slug(request)

        try:
            self.user_perms = set([self.user_perms['reposit'
                                                   'ories'][self.repo_name]])
        except KeyError:
            return False
        self.granted_for = self.repo_name
        if self.required_perms.issubset(self.user_perms):
            return True
        return False


class HasRepoPermissionAny(PermsFunction):

    def __call__(self, repo_name=None, check_Location=''):
        self.repo_name = repo_name
        return super(HasRepoPermissionAny, self).__call__(check_Location)

    def check_permissions(self):
        if not self.repo_name:
            self.repo_name = get_repo_slug(request)

        try:
            self.user_perms = set([self.user_perms['reposi'
                                                   'tories'][self.repo_name]])
        except KeyError:
            return False
        self.granted_for = self.repo_name
        if self.required_perms.intersection(self.user_perms):
            return True
        return False


#==============================================================================
# SPECIAL VERSION TO HANDLE MIDDLEWARE AUTH
#==============================================================================
class HasPermissionAnyMiddleware(object):
    def __init__(self, *perms):
        self.required_perms = set(perms)

    def __call__(self, user, repo_name):
        usr = AuthUser(user.user_id)
        try:
            self.user_perms = set([usr.permissions['repositories'][repo_name]])
        except:
            self.user_perms = set()
        self.granted_for = ''
        self.username = user.username
        self.repo_name = repo_name
        return self.check_permissions()

    def check_permissions(self):
        log.debug('checking mercurial protocol '
                  'permissions %s for user:%s repository:%s', self.user_perms,
                                                self.username, self.repo_name)
        if self.required_perms.intersection(self.user_perms):
            log.debug('permission granted')
            return True
        log.debug('permission denied')
        return False
