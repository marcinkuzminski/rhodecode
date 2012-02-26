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
import traceback

import formencode
from formencode import All
from formencode.validators import UnicodeString, OneOf, Int, Number, Regex, \
    Email, Bool, StringBoolean, Set

from pylons.i18n.translation import _
from webhelpers.pylonslib.secure_form import authentication_token

from rhodecode.config.routing import ADMIN_PREFIX
from rhodecode.lib.utils import repo_name_slug
from rhodecode.lib.auth import authenticate, get_crypt_password
from rhodecode.lib.exceptions import LdapImportError
from rhodecode.model.db import User, UsersGroup, RepoGroup, Repository
from rhodecode import BACKENDS

log = logging.getLogger(__name__)


#this is needed to translate the messages using _() in validators
class State_obj(object):
    _ = staticmethod(_)


#==============================================================================
# VALIDATORS
#==============================================================================
class ValidAuthToken(formencode.validators.FancyValidator):
    messages = {'invalid_token': _('Token mismatch')}

    def validate_python(self, value, state):

        if value != authentication_token():
            raise formencode.Invalid(
                self.message('invalid_token',
                             state, search_number=value),
                value,
                state
            )


def ValidUsername(edit, old_data):
    class _ValidUsername(formencode.validators.FancyValidator):

        def validate_python(self, value, state):
            if value in ['default', 'new_user']:
                raise formencode.Invalid(_('Invalid username'), value, state)
            #check if user is unique
            old_un = None
            if edit:
                old_un = User.get(old_data.get('user_id')).username

            if old_un != value or not edit:
                if User.get_by_username(value, case_insensitive=True):
                    raise formencode.Invalid(_('This username already '
                                               'exists') , value, state)

            if re.match(r'^[a-zA-Z0-9]{1}[a-zA-Z0-9\-\_\.]+$', value) is None:
                raise formencode.Invalid(
                    _('Username may only contain alphanumeric characters '
                      'underscores, periods or dashes and must begin with '
                      'alphanumeric character'),
                    value,
                    state
                )

    return _ValidUsername


def ValidUsersGroup(edit, old_data):

    class _ValidUsersGroup(formencode.validators.FancyValidator):

        def validate_python(self, value, state):
            if value in ['default']:
                raise formencode.Invalid(_('Invalid group name'), value, state)
            #check if group is unique
            old_ugname = None
            if edit:
                old_ugname = UsersGroup.get(
                            old_data.get('users_group_id')).users_group_name

            if old_ugname != value or not edit:
                if UsersGroup.get_by_group_name(value, cache=False,
                                               case_insensitive=True):
                    raise formencode.Invalid(_('This users group '
                                               'already exists'), value,
                                             state)

            if re.match(r'^[a-zA-Z0-9]{1}[a-zA-Z0-9\-\_\.]+$', value) is None:
                raise formencode.Invalid(
                    _('RepoGroup name may only contain  alphanumeric characters '
                      'underscores, periods or dashes and must begin with '
                      'alphanumeric character'),
                    value,
                    state
                )

    return _ValidUsersGroup


def ValidReposGroup(edit, old_data):
    class _ValidReposGroup(formencode.validators.FancyValidator):

        def validate_python(self, value, state):
            # TODO WRITE VALIDATIONS
            group_name = value.get('group_name')
            group_parent_id = value.get('group_parent_id')

            # slugify repo group just in case :)
            slug = repo_name_slug(group_name)

            # check for parent of self
            parent_of_self = lambda: (
                old_data['group_id'] == int(group_parent_id)
                if group_parent_id else False
            )
            if edit and parent_of_self():
                    e_dict = {
                        'group_parent_id': _('Cannot assign this group as parent')
                    }
                    raise formencode.Invalid('', value, state,
                                             error_dict=e_dict)

            old_gname = None
            if edit:
                old_gname = RepoGroup.get(old_data.get('group_id')).group_name

            if old_gname != group_name or not edit:

                # check group
                gr = RepoGroup.query()\
                      .filter(RepoGroup.group_name == slug)\
                      .filter(RepoGroup.group_parent_id == group_parent_id)\
                      .scalar()

                if gr:
                    e_dict = {
                        'group_name': _('This group already exists')
                    }
                    raise formencode.Invalid('', value, state,
                                             error_dict=e_dict)

                # check for same repo
                repo = Repository.query()\
                      .filter(Repository.repo_name == slug)\
                      .scalar()

                if repo:
                    e_dict = {
                        'group_name': _('Repository with this name already exists')
                    }
                    raise formencode.Invalid('', value, state,
                                             error_dict=e_dict)

    return _ValidReposGroup


class ValidPassword(formencode.validators.FancyValidator):

    def to_python(self, value, state):

        if not value:
            return

        if value.get('password'):
            try:
                value['password'] = get_crypt_password(value['password'])
            except UnicodeEncodeError:
                e_dict = {'password': _('Invalid characters in password')}
                raise formencode.Invalid('', value, state, error_dict=e_dict)

        if value.get('password_confirmation'):
            try:
                value['password_confirmation'] = \
                    get_crypt_password(value['password_confirmation'])
            except UnicodeEncodeError:
                e_dict = {
                    'password_confirmation': _('Invalid characters in password')
                }
                raise formencode.Invalid('', value, state, error_dict=e_dict)

        if value.get('new_password'):
            try:
                value['new_password'] = \
                    get_crypt_password(value['new_password'])
            except UnicodeEncodeError:
                e_dict = {'new_password': _('Invalid characters in password')}
                raise formencode.Invalid('', value, state, error_dict=e_dict)

        return value


class ValidPasswordsMatch(formencode.validators.FancyValidator):

    def validate_python(self, value, state):

        pass_val = value.get('password') or value.get('new_password')
        if pass_val != value['password_confirmation']:
            e_dict = {'password_confirmation':
                   _('Passwords do not match')}
            raise formencode.Invalid('', value, state, error_dict=e_dict)


class ValidAuth(formencode.validators.FancyValidator):
    messages = {
        'invalid_password':_('invalid password'),
        'invalid_login':_('invalid user name'),
        'disabled_account':_('Your account is disabled')
    }

    # error mapping
    e_dict = {'username': messages['invalid_login'],
              'password': messages['invalid_password']}
    e_dict_disable = {'username': messages['disabled_account']}

    def validate_python(self, value, state):
        password = value['password']
        username = value['username']
        user = User.get_by_username(username)

        if authenticate(username, password):
            return value
        else:
            if user and user.active is False:
                log.warning('user %s is disabled' % username)
                raise formencode.Invalid(
                    self.message('disabled_account',
                    state=State_obj),
                    value, state,
                    error_dict=self.e_dict_disable
                )
            else:
                log.warning('user %s failed to authenticate' % username)
                raise formencode.Invalid(
                    self.message('invalid_password',
                    state=State_obj), value, state,
                    error_dict=self.e_dict
                )


class ValidRepoUser(formencode.validators.FancyValidator):

    def to_python(self, value, state):
        try:
            User.query().filter(User.active == True)\
                .filter(User.username == value).one()
        except Exception:
            raise formencode.Invalid(_('This username is not valid'),
                                     value, state)
        return value


def ValidRepoName(edit, old_data):
    class _ValidRepoName(formencode.validators.FancyValidator):
        def to_python(self, value, state):

            repo_name = value.get('repo_name')

            slug = repo_name_slug(repo_name)
            if slug in [ADMIN_PREFIX, '']:
                e_dict = {'repo_name': _('This repository name is disallowed')}
                raise formencode.Invalid('', value, state, error_dict=e_dict)

            if value.get('repo_group'):
                gr = RepoGroup.get(value.get('repo_group'))
                group_path = gr.full_path
                # value needs to be aware of group name in order to check
                # db key This is an actual just the name to store in the
                # database
                repo_name_full = group_path + RepoGroup.url_sep() + repo_name

            else:
                group_path = ''
                repo_name_full = repo_name

            value['repo_name_full'] = repo_name_full
            rename = old_data.get('repo_name') != repo_name_full
            create = not edit
            if  rename or create:

                if group_path != '':
                    if Repository.get_by_repo_name(repo_name_full):
                        e_dict = {
                            'repo_name': _('This repository already exists in '
                                           'a group "%s"') % gr.group_name
                        }
                        raise formencode.Invalid('', value, state,
                                                 error_dict=e_dict)
                elif RepoGroup.get_by_group_name(repo_name_full):
                        e_dict = {
                            'repo_name': _('There is a group with this name '
                                           'already "%s"') % repo_name_full
                        }
                        raise formencode.Invalid('', value, state,
                                                 error_dict=e_dict)

                elif Repository.get_by_repo_name(repo_name_full):
                        e_dict = {'repo_name': _('This repository '
                                                'already exists')}
                        raise formencode.Invalid('', value, state,
                                                 error_dict=e_dict)

            return value

    return _ValidRepoName


def ValidForkName(*args, **kwargs):
    return ValidRepoName(*args, **kwargs)


def SlugifyName():
    class _SlugifyName(formencode.validators.FancyValidator):

        def to_python(self, value, state):
            return repo_name_slug(value)

    return _SlugifyName


def ValidCloneUri():
    from mercurial.httprepo import httprepository, httpsrepository
    from rhodecode.lib.utils import make_ui

    class _ValidCloneUri(formencode.validators.FancyValidator):

        def to_python(self, value, state):
            if not value:
                pass
            elif value.startswith('https'):
                try:
                    httpsrepository(make_ui('db'), value).capabilities
                except Exception:
                    log.error(traceback.format_exc())
                    raise formencode.Invalid(_('invalid clone url'), value,
                                             state)
            elif value.startswith('http'):
                try:
                    httprepository(make_ui('db'), value).capabilities
                except Exception:
                    log.error(traceback.format_exc())
                    raise formencode.Invalid(_('invalid clone url'), value,
                                             state)
            else:
                raise formencode.Invalid(_('Invalid clone url, provide a '
                                           'valid clone http\s url'), value,
                                         state)
            return value

    return _ValidCloneUri


def ValidForkType(old_data):
    class _ValidForkType(formencode.validators.FancyValidator):

        def to_python(self, value, state):
            if old_data['repo_type'] != value:
                raise formencode.Invalid(_('Fork have to be the same '
                                           'type as original'), value, state)

            return value
    return _ValidForkType


def ValidPerms(type_='repo'):
    if type_ == 'group':
        EMPTY_PERM = 'group.none'
    elif type_ == 'repo':
        EMPTY_PERM = 'repository.none'

    class _ValidPerms(formencode.validators.FancyValidator):
        messages = {
            'perm_new_member_name':
                _('This username or users group name is not valid')
        }

        def to_python(self, value, state):
            perms_update = []
            perms_new = []
            # build a list of permission to update and new permission to create
            for k, v in value.items():
                # means new added member to permissions
                if k.startswith('perm_new_member'):
                    new_perm = value.get('perm_new_member', False)
                    new_member = value.get('perm_new_member_name', False)
                    new_type = value.get('perm_new_member_type')

                    if new_member and new_perm:
                        if (new_member, new_perm, new_type) not in perms_new:
                            perms_new.append((new_member, new_perm, new_type))
                elif k.startswith('u_perm_') or k.startswith('g_perm_'):
                    member = k[7:]
                    t = {'u': 'user',
                         'g': 'users_group'
                    }[k[0]]
                    if member == 'default':
                        if value.get('private'):
                            # set none for default when updating to private repo
                            v = EMPTY_PERM
                    perms_update.append((member, v, t))

            value['perms_updates'] = perms_update
            value['perms_new'] = perms_new

            # update permissions
            for k, v, t in perms_new:
                try:
                    if t is 'user':
                        self.user_db = User.query()\
                            .filter(User.active == True)\
                            .filter(User.username == k).one()
                    if t is 'users_group':
                        self.user_db = UsersGroup.query()\
                            .filter(UsersGroup.users_group_active == True)\
                            .filter(UsersGroup.users_group_name == k).one()

                except Exception:
                    msg = self.message('perm_new_member_name',
                                         state=State_obj)
                    raise formencode.Invalid(
                        msg, value, state, error_dict={'perm_new_member_name': msg}
                    )
            return value
    return _ValidPerms


class ValidSettings(formencode.validators.FancyValidator):

    def to_python(self, value, state):
        # settings  form can't edit user
        if 'user' in value:
            del['value']['user']
        return value


class ValidPath(formencode.validators.FancyValidator):
    def to_python(self, value, state):

        if not os.path.isdir(value):
            msg = _('This is not a valid path')
            raise formencode.Invalid(msg, value, state,
                                     error_dict={'paths_root_path': msg})
        return value


def UniqSystemEmail(old_data):
    class _UniqSystemEmail(formencode.validators.FancyValidator):
        def to_python(self, value, state):
            value = value.lower()
            if old_data.get('email', '').lower() != value:
                user = User.get_by_email(value, case_insensitive=True)
                if user:
                    raise formencode.Invalid(
                        _("This e-mail address is already taken"), value, state
                    )
            return value

    return _UniqSystemEmail


class ValidSystemEmail(formencode.validators.FancyValidator):
    def to_python(self, value, state):
        value = value.lower()
        user = User.get_by_email(value, case_insensitive=True)
        if  user is None:
            raise formencode.Invalid(
                _("This e-mail address doesn't exist."), value, state
            )

        return value


class LdapLibValidator(formencode.validators.FancyValidator):

    def to_python(self, value, state):

        try:
            import ldap
        except ImportError:
            raise LdapImportError
        return value


class AttrLoginValidator(formencode.validators.FancyValidator):

    def to_python(self, value, state):

        if not value or not isinstance(value, (str, unicode)):
            raise formencode.Invalid(
                _("The LDAP Login attribute of the CN must be specified - "
                  "this is the name of the attribute that is equivalent "
                  "to 'username'"), value, state
            )

        return value


#==============================================================================
# FORMS
#==============================================================================
class LoginForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    username = UnicodeString(
        strip=True,
        min=1,
        not_empty=True,
        messages={
           'empty': _('Please enter a login'),
           'tooShort': _('Enter a value %(min)i characters long or more')}
    )

    password = UnicodeString(
        strip=True,
        min=3,
        not_empty=True,
        messages={
            'empty': _('Please enter a password'),
            'tooShort': _('Enter %(min)i characters or more')}
    )

    remember = StringBoolean(if_missing=False)

    chained_validators = [ValidAuth]


def UserForm(edit=False, old_data={}):
    class _UserForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(UnicodeString(strip=True, min=1, not_empty=True),
                       ValidUsername(edit, old_data))
        if edit:
            new_password = All(UnicodeString(strip=True, min=6, not_empty=False))
            password_confirmation = All(UnicodeString(strip=True, min=6,
                                                      not_empty=False))
            admin = StringBoolean(if_missing=False)
        else:
            password = All(UnicodeString(strip=True, min=6, not_empty=True))
            password_confirmation = All(UnicodeString(strip=True, min=6,
                                                      not_empty=False))

        active = StringBoolean(if_missing=False)
        name = UnicodeString(strip=True, min=1, not_empty=False)
        lastname = UnicodeString(strip=True, min=1, not_empty=False)
        email = All(Email(not_empty=True), UniqSystemEmail(old_data))

        chained_validators = [ValidPasswordsMatch, ValidPassword]

    return _UserForm


def UsersGroupForm(edit=False, old_data={}, available_members=[]):
    class _UsersGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        users_group_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                       ValidUsersGroup(edit, old_data))

        users_group_active = StringBoolean(if_missing=False)

        if edit:
            users_group_members = OneOf(available_members, hideList=False,
                                        testValueList=True,
                                        if_missing=None, not_empty=False)

    return _UsersGroupForm


def ReposGroupForm(edit=False, old_data={}, available_groups=[]):
    class _ReposGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False

        group_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                               SlugifyName())
        group_description = UnicodeString(strip=True, min=1,
                                                not_empty=True)
        group_parent_id = OneOf(available_groups, hideList=False,
                                        testValueList=True,
                                        if_missing=None, not_empty=False)

        chained_validators = [ValidReposGroup(edit, old_data), ValidPerms('group')]

    return _ReposGroupForm


def RegisterForm(edit=False, old_data={}):
    class _RegisterForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(ValidUsername(edit, old_data),
                       UnicodeString(strip=True, min=1, not_empty=True))
        password = All(UnicodeString(strip=True, min=6, not_empty=True))
        password_confirmation = All(UnicodeString(strip=True, min=6, not_empty=True))
        active = StringBoolean(if_missing=False)
        name = UnicodeString(strip=True, min=1, not_empty=False)
        lastname = UnicodeString(strip=True, min=1, not_empty=False)
        email = All(Email(not_empty=True), UniqSystemEmail(old_data))

        chained_validators = [ValidPasswordsMatch, ValidPassword]

    return _RegisterForm


def PasswordResetForm():
    class _PasswordResetForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        email = All(ValidSystemEmail(), Email(not_empty=True))
    return _PasswordResetForm


def RepoForm(edit=False, old_data={}, supported_backends=BACKENDS.keys(),
             repo_groups=[]):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                        SlugifyName())
        clone_uri = All(UnicodeString(strip=True, min=1, not_empty=False),
                        ValidCloneUri()())
        repo_group = OneOf(repo_groups, hideList=True)
        repo_type = OneOf(supported_backends)
        description = UnicodeString(strip=True, min=1, not_empty=True)
        private = StringBoolean(if_missing=False)
        enable_statistics = StringBoolean(if_missing=False)
        enable_downloads = StringBoolean(if_missing=False)

        if edit:
            #this is repo owner
            user = All(UnicodeString(not_empty=True), ValidRepoUser)

        chained_validators = [ValidRepoName(edit, old_data), ValidPerms()]
    return _RepoForm


def RepoForkForm(edit=False, old_data={}, supported_backends=BACKENDS.keys(),
                 repo_groups=[]):
    class _RepoForkForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                        SlugifyName())
        repo_group = OneOf(repo_groups, hideList=True)
        repo_type = All(ValidForkType(old_data), OneOf(supported_backends))
        description = UnicodeString(strip=True, min=1, not_empty=True)
        private = StringBoolean(if_missing=False)
        copy_permissions = StringBoolean(if_missing=False)
        update_after_clone = StringBoolean(if_missing=False)
        fork_parent_id = UnicodeString()
        chained_validators = [ValidForkName(edit, old_data)]

    return _RepoForkForm


def RepoSettingsForm(edit=False, old_data={}, supported_backends=BACKENDS.keys(),
                     repo_groups=[]):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True),
                        SlugifyName())
        description = UnicodeString(strip=True, min=1, not_empty=True)
        repo_group = OneOf(repo_groups, hideList=True)
        private = StringBoolean(if_missing=False)

        chained_validators = [ValidRepoName(edit, old_data), ValidPerms(),
                              ValidSettings]
    return _RepoForm


def ApplicationSettingsForm():
    class _ApplicationSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        rhodecode_title = UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_realm = UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_ga_code = UnicodeString(strip=True, min=1, not_empty=False)

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


def LdapSettingsForm(tls_reqcert_choices, search_scope_choices, tls_kind_choices):
    class _LdapSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        pre_validators = [LdapLibValidator]
        ldap_active = StringBoolean(if_missing=False)
        ldap_host = UnicodeString(strip=True,)
        ldap_port = Number(strip=True,)
        ldap_tls_kind = OneOf(tls_kind_choices)
        ldap_tls_reqcert = OneOf(tls_reqcert_choices)
        ldap_dn_user = UnicodeString(strip=True,)
        ldap_dn_pass = UnicodeString(strip=True,)
        ldap_base_dn = UnicodeString(strip=True,)
        ldap_filter = UnicodeString(strip=True,)
        ldap_search_scope = OneOf(search_scope_choices)
        ldap_attr_login = All(AttrLoginValidator, UnicodeString(strip=True,))
        ldap_attr_firstname = UnicodeString(strip=True,)
        ldap_attr_lastname = UnicodeString(strip=True,)
        ldap_attr_email = UnicodeString(strip=True,)

    return _LdapSettingsForm
