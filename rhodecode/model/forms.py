""" this is forms validation classes
http://formencode.org/module-formencode.validators.html
for list off all availible validators

we can create our own validators

The table below outlines the options which can be used in a schema in addition to the validators themselves
pre_validators          []     These validators will be applied before the schema
chained_validators      []     These validators will be applied after the schema
allow_extra_fields      False     If True, then it is not an error when keys that aren't associated with a validator are present
filter_extra_fields     False     If True, then keys that aren't associated with a validator are removed
if_key_missing          NoDefault If this is given, then any keys that aren't available but are expected will be replaced with this value (and then validated). This does not override a present .if_missing attribute on validators. NoDefault is a special FormEncode class to mean that no default values has been specified and therefore missing keys shouldn't take a default value.
ignore_key_missing      False     If True, then missing keys will be missing in the result, if the validator doesn't have .if_missing on it already    
  
  
<name> = formencode.validators.<name of validator>
<name> must equal form name
list=[1,2,3,4,5]
for SELECT use formencode.All(OneOf(list), Int())
    
"""
import os
import re
import logging

import formencode
from formencode import All
from formencode.validators import UnicodeString, OneOf, Int, Number, Regex, \
    Email, Bool, StringBoolean

from pylons.i18n.translation import _

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import authenticate, get_crypt_password
from rhodecode.lib.exceptions import LdapImportError
from rhodecode.model import meta
from rhodecode.model.user import UserModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import User
from rhodecode import BACKENDS

from webhelpers.pylonslib.secure_form import authentication_token

log = logging.getLogger(__name__)

#this is needed to translate the messages using _() in validators
class State_obj(object):
    _ = staticmethod(_)

#===============================================================================
# VALIDATORS
#===============================================================================
class ValidAuthToken(formencode.validators.FancyValidator):
    messages = {'invalid_token':_('Token mismatch')}

    def validate_python(self, value, state):

        if value != authentication_token():
            raise formencode.Invalid(self.message('invalid_token', state,
                                            search_number=value), value, state)

def ValidUsername(edit, old_data):
    class _ValidUsername(formencode.validators.FancyValidator):

        def validate_python(self, value, state):
            if value in ['default', 'new_user']:
                raise formencode.Invalid(_('Invalid username'), value, state)
            #check if user is unique
            old_un = None
            if edit:
                old_un = UserModel().get(old_data.get('user_id')).username

            if old_un != value or not edit:
                if UserModel().get_by_username(value, cache=False,
                                               case_insensitive=True):
                    raise formencode.Invalid(_('This username already exists') ,
                                             value, state)


            if re.match(r'^[a-zA-Z0-9]{1}[a-zA-Z0-9\-\_]+$', value) is None:
                raise formencode.Invalid(_('Username may only contain '
                                           'alphanumeric characters underscores '
                                           'or dashes and must begin with '
                                           'alphanumeric character'),
                                      value, state)



    return _ValidUsername

class ValidPassword(formencode.validators.FancyValidator):

    def to_python(self, value, state):

        if value:

            if value.get('password'):
                try:
                    value['password'] = get_crypt_password(value['password'])
                except UnicodeEncodeError:
                    e_dict = {'password':_('Invalid characters in password')}
                    raise formencode.Invalid('', value, state, error_dict=e_dict)

            if value.get('password_confirmation'):
                try:
                    value['password_confirmation'] = \
                        get_crypt_password(value['password_confirmation'])
                except UnicodeEncodeError:
                    e_dict = {'password_confirmation':_('Invalid characters in password')}
                    raise formencode.Invalid('', value, state, error_dict=e_dict)

            if value.get('new_password'):
                try:
                    value['new_password'] = \
                        get_crypt_password(value['new_password'])
                except UnicodeEncodeError:
                    e_dict = {'new_password':_('Invalid characters in password')}
                    raise formencode.Invalid('', value, state, error_dict=e_dict)

            return value

class ValidPasswordsMatch(formencode.validators.FancyValidator):

    def validate_python(self, value, state):

        if value['password'] != value['password_confirmation']:
            e_dict = {'password_confirmation':
                   _('Password do not match')}
            raise formencode.Invalid('', value, state, error_dict=e_dict)

class ValidAuth(formencode.validators.FancyValidator):
    messages = {
            'invalid_password':_('invalid password'),
            'invalid_login':_('invalid user name'),
            'disabled_account':_('Your account is disabled')

            }
    #error mapping
    e_dict = {'username':messages['invalid_login'],
              'password':messages['invalid_password']}
    e_dict_disable = {'username':messages['disabled_account']}

    def validate_python(self, value, state):
        password = value['password']
        username = value['username']
        user = UserModel().get_by_username(username)

        if authenticate(username, password):
            return value
        else:
            if user and user.active is False:
                log.warning('user %s is disabled', username)
                raise formencode.Invalid(self.message('disabled_account',
                                         state=State_obj),
                                         value, state,
                                         error_dict=self.e_dict_disable)
            else:
                log.warning('user %s not authenticated', username)
                raise formencode.Invalid(self.message('invalid_password',
                                         state=State_obj), value, state,
                                         error_dict=self.e_dict)

class ValidRepoUser(formencode.validators.FancyValidator):

    def to_python(self, value, state):
        sa = meta.Session()
        try:
            self.user_db = sa.query(User)\
                .filter(User.active == True)\
                .filter(User.username == value).one()
        except Exception:
            raise formencode.Invalid(_('This username is not valid'),
                                     value, state)
        finally:
            meta.Session.remove()

        return self.user_db.user_id

def ValidRepoName(edit, old_data):
    class _ValidRepoName(formencode.validators.FancyValidator):

        def to_python(self, value, state):
            slug = h.repo_name_slug(value)
            if slug in ['_admin']:
                raise formencode.Invalid(_('This repository name is disallowed'),
                                         value, state)
            if old_data.get('repo_name') != value or not edit:
                if RepoModel().get_by_repo_name(slug, cache=False):
                    raise formencode.Invalid(_('This repository already exists') ,
                                             value, state)
            return slug


    return _ValidRepoName

def ValidForkType(old_data):
    class _ValidForkType(formencode.validators.FancyValidator):

        def to_python(self, value, state):
            if old_data['repo_type'] != value:
                raise formencode.Invalid(_('Fork have to be the same type as original'),
                                         value, state)
            return value
    return _ValidForkType

class ValidPerms(formencode.validators.FancyValidator):
    messages = {'perm_new_user_name':_('This username is not valid')}

    def to_python(self, value, state):
        perms_update = []
        perms_new = []
        #build a list of permission to update and new permission to create
        for k, v in value.items():
            if k.startswith('perm_'):
                if  k.startswith('perm_new_user'):
                    new_perm = value.get('perm_new_user', False)
                    new_user = value.get('perm_new_user_name', False)
                    if new_user and new_perm:
                        if (new_user, new_perm) not in perms_new:
                            perms_new.append((new_user, new_perm))
                else:
                    usr = k[5:]
                    if usr == 'default':
                        if value['private']:
                            #set none for default when updating to private repo
                            v = 'repository.none'
                    perms_update.append((usr, v))
        value['perms_updates'] = perms_update
        value['perms_new'] = perms_new
        sa = meta.Session
        for k, v in perms_new:
            try:
                self.user_db = sa.query(User)\
                    .filter(User.active == True)\
                    .filter(User.username == k).one()
            except Exception:
                msg = self.message('perm_new_user_name',
                                     state=State_obj)
                raise formencode.Invalid(msg, value, state,
                                         error_dict={'perm_new_user_name':msg})
        return value

class ValidSettings(formencode.validators.FancyValidator):

    def to_python(self, value, state):
        #settings  form can't edit user
        if value.has_key('user'):
            del['value']['user']

        return value

class ValidPath(formencode.validators.FancyValidator):
    def to_python(self, value, state):

        if not os.path.isdir(value):
            msg = _('This is not a valid path')
            raise formencode.Invalid(msg, value, state,
                                     error_dict={'paths_root_path':msg})
        return value

def UniqSystemEmail(old_data):
    class _UniqSystemEmail(formencode.validators.FancyValidator):
        def to_python(self, value, state):
            value = value.lower()
            if old_data.get('email') != value:
                sa = meta.Session()
                try:
                    user = sa.query(User).filter(User.email == value).scalar()
                    if user:
                        raise formencode.Invalid(_("This e-mail address is already taken") ,
                                                 value, state)
                finally:
                    meta.Session.remove()

            return value

    return _UniqSystemEmail

class ValidSystemEmail(formencode.validators.FancyValidator):
    def to_python(self, value, state):
        value = value.lower()
        sa = meta.Session
        try:
            user = sa.query(User).filter(User.email == value).scalar()
            if  user is None:
                raise formencode.Invalid(_("This e-mail address doesn't exist.") ,
                                         value, state)
        finally:
            meta.Session.remove()

        return value

class LdapLibValidator(formencode.validators.FancyValidator):

    def to_python(self, value, state):

        try:
            import ldap
        except ImportError:
            raise LdapImportError
        return value

class BaseDnValidator(formencode.validators.FancyValidator):

    def to_python(self, value, state):

        try:
            value % {'user':'valid'}

            if value.find('%(user)s') == -1:
                raise formencode.Invalid(_("You need to specify %(user)s in "
                                           "template for example uid=%(user)s "
                                           ",dc=company...") ,
                                         value, state)

        except KeyError:
            raise formencode.Invalid(_("Wrong template used, only %(user)s "
                                       "is an valid entry") ,
                                         value, state)

        return value

#===============================================================================
# FORMS        
#===============================================================================
class LoginForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    username = UnicodeString(
                             strip=True,
                             min=1,
                             not_empty=True,
                             messages={
                                       'empty':_('Please enter a login'),
                                       'tooShort':_('Enter a value %(min)i characters long or more')}
                            )

    password = UnicodeString(
                            strip=True,
                            min=6,
                            not_empty=True,
                            messages={
                                      'empty':_('Please enter a password'),
                                      'tooShort':_('Enter %(min)i characters or more')}
                                )


    #chained validators have access to all data
    chained_validators = [ValidAuth]

def UserForm(edit=False, old_data={}):
    class _UserForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(UnicodeString(strip=True, min=1, not_empty=True),
                       ValidUsername(edit, old_data))
        if edit:
            new_password = All(UnicodeString(strip=True, min=6, not_empty=False))
            admin = StringBoolean(if_missing=False)
        else:
            password = All(UnicodeString(strip=True, min=6, not_empty=True))
        active = StringBoolean(if_missing=False)
        name = UnicodeString(strip=True, min=1, not_empty=True)
        lastname = UnicodeString(strip=True, min=1, not_empty=True)
        email = All(Email(not_empty=True), UniqSystemEmail(old_data))

        chained_validators = [ValidPassword]

    return _UserForm

def RegisterForm(edit=False, old_data={}):
    class _RegisterForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(ValidUsername(edit, old_data),
                       UnicodeString(strip=True, min=1, not_empty=True))
        password = All(UnicodeString(strip=True, min=6, not_empty=True))
        password_confirmation = All(UnicodeString(strip=True, min=6, not_empty=True))
        active = StringBoolean(if_missing=False)
        name = UnicodeString(strip=True, min=1, not_empty=True)
        lastname = UnicodeString(strip=True, min=1, not_empty=True)
        email = All(Email(not_empty=True), UniqSystemEmail(old_data))

        chained_validators = [ValidPasswordsMatch, ValidPassword]

    return _RegisterForm

def PasswordResetForm():
    class _PasswordResetForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        email = All(ValidSystemEmail(), Email(not_empty=True))
    return _PasswordResetForm

def RepoForm(edit=False, old_data={}, supported_backends=BACKENDS.keys()):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                        ValidRepoName(edit, old_data))
        description = UnicodeString(strip=True, min=1, not_empty=True)
        private = StringBoolean(if_missing=False)
        enable_statistics = StringBoolean(if_missing=False)
        repo_type = OneOf(supported_backends)
        if edit:
            user = All(Int(not_empty=True), ValidRepoUser)

        chained_validators = [ValidPerms]
    return _RepoForm

def RepoForkForm(edit=False, old_data={}, supported_backends=BACKENDS.keys()):
    class _RepoForkForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        fork_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                        ValidRepoName(edit, old_data))
        description = UnicodeString(strip=True, min=1, not_empty=True)
        private = StringBoolean(if_missing=False)
        repo_type = All(ValidForkType(old_data), OneOf(supported_backends))
    return _RepoForkForm

def RepoSettingsForm(edit=False, old_data={}):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                        ValidRepoName(edit, old_data))
        description = UnicodeString(strip=True, min=1, not_empty=True)
        private = StringBoolean(if_missing=False)

        chained_validators = [ValidPerms, ValidSettings]
    return _RepoForm


def ApplicationSettingsForm():
    class _ApplicationSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        rhodecode_title = UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_realm = UnicodeString(strip=True, min=1, not_empty=True)
        ga_code = UnicodeString(strip=True, min=1, not_empty=False)

    return _ApplicationSettingsForm

def ApplicationUiSettingsForm():
    class _ApplicationUiSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        web_push_ssl = OneOf(['true', 'false'], if_missing='false')
        paths_root_path = All(ValidPath(), UnicodeString(strip=True, min=1, not_empty=True))
        hooks_changegroup_update = OneOf(['True', 'False'], if_missing=False)
        hooks_changegroup_repo_size = OneOf(['True', 'False'], if_missing=False)
        hooks_pretxnchangegroup_push_logger = OneOf(['True', 'False'], if_missing=False)
        hooks_preoutgoing_pull_logger = OneOf(['True', 'False'], if_missing=False)

    return _ApplicationUiSettingsForm

def DefaultPermissionsForm(perms_choices, register_choices, create_choices):
    class _DefaultPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        overwrite_default = StringBoolean(if_missing=False)
        anonymous = OneOf(['True', 'False'], if_missing=False)
        default_perm = OneOf(perms_choices)
        default_register = OneOf(register_choices)
        default_create = OneOf(create_choices)

    return _DefaultPermissionsForm


def LdapSettingsForm():
    class _LdapSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        pre_validators = [LdapLibValidator]
        ldap_active = StringBoolean(if_missing=False)
        ldap_host = UnicodeString(strip=True,)
        ldap_port = Number(strip=True,)
        ldap_ldaps = StringBoolean(if_missing=False)
        ldap_dn_user = UnicodeString(strip=True,)
        ldap_dn_pass = UnicodeString(strip=True,)
        ldap_base_dn = All(BaseDnValidator, UnicodeString(strip=True,))

    return _LdapSettingsForm
