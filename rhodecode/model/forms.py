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
import logging

import formencode
from formencode import All

from pylons.i18n.translation import _

from rhodecode.model import validators as v
from rhodecode import BACKENDS

log = logging.getLogger(__name__)


class LoginForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    username = v.UnicodeString(
        strip=True,
        min=1,
        not_empty=True,
        messages={
           'empty': _(u'Please enter a login'),
           'tooShort': _(u'Enter a value %(min)i characters long or more')}
    )

    password = v.UnicodeString(
        strip=False,
        min=3,
        not_empty=True,
        messages={
            'empty': _(u'Please enter a password'),
            'tooShort': _(u'Enter %(min)i characters or more')}
    )

    remember = v.StringBoolean(if_missing=False)

    chained_validators = [v.ValidAuth()]


def UserForm(edit=False, old_data={}):
    class _UserForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                       v.ValidUsername(edit, old_data))
        if edit:
            new_password = All(
                v.UnicodeString(strip=False, min=6, not_empty=False)
            )
            password_confirmation = All(
                v.ValidPassword(),
                v.UnicodeString(strip=False, min=6, not_empty=False),
            )
            admin = v.StringBoolean(if_missing=False)
        else:
            password = All(
                v.ValidPassword(),
                v.UnicodeString(strip=False, min=6, not_empty=True)
            )
            password_confirmation = All(
                v.ValidPassword(),
                v.UnicodeString(strip=False, min=6, not_empty=False)
            )

        active = v.StringBoolean(if_missing=False)
        name = v.UnicodeString(strip=True, min=1, not_empty=False)
        lastname = v.UnicodeString(strip=True, min=1, not_empty=False)
        email = All(v.Email(not_empty=True), v.UniqSystemEmail(old_data))

        chained_validators = [v.ValidPasswordsMatch()]

    return _UserForm


def UsersGroupForm(edit=False, old_data={}, available_members=[]):
    class _UsersGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        users_group_name = All(
            v.UnicodeString(strip=True, min=1, not_empty=True),
            v.ValidUsersGroup(edit, old_data)
        )

        users_group_active = v.StringBoolean(if_missing=False)

        if edit:
            users_group_members = v.OneOf(
                available_members, hideList=False, testValueList=True,
                if_missing=None, not_empty=False
            )

    return _UsersGroupForm


def ReposGroupForm(edit=False, old_data={}, available_groups=[]):
    class _ReposGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False

        group_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                               v.SlugifyName())
        group_description = v.UnicodeString(strip=True, min=1,
                                                not_empty=True)
        group_parent_id = v.OneOf(available_groups, hideList=False,
                                        testValueList=True,
                                        if_missing=None, not_empty=False)

        chained_validators = [v.ValidReposGroup(edit, old_data),
                              v.ValidPerms('group')]

    return _ReposGroupForm


def RegisterForm(edit=False, old_data={}):
    class _RegisterForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(
            v.ValidUsername(edit, old_data),
            v.UnicodeString(strip=True, min=1, not_empty=True)
        )
        password = All(
            v.ValidPassword(),
            v.UnicodeString(strip=False, min=6, not_empty=True)
        )
        password_confirmation = All(
            v.ValidPassword(),
            v.UnicodeString(strip=False, min=6, not_empty=True)
        )
        active = v.StringBoolean(if_missing=False)
        name = v.UnicodeString(strip=True, min=1, not_empty=False)
        lastname = v.UnicodeString(strip=True, min=1, not_empty=False)
        email = All(v.Email(not_empty=True), v.UniqSystemEmail(old_data))

        chained_validators = [v.ValidPasswordsMatch()]

    return _RegisterForm


def PasswordResetForm():
    class _PasswordResetForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        email = All(v.ValidSystemEmail(), v.Email(not_empty=True))
    return _PasswordResetForm


def RepoForm(edit=False, old_data={}, supported_backends=BACKENDS.keys(),
             repo_groups=[], landing_revs=[]):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                        v.SlugifyName())
        clone_uri = All(v.UnicodeString(strip=True, min=1, not_empty=False))
        repo_group = v.OneOf(repo_groups, hideList=True)
        repo_type = v.OneOf(supported_backends)
        description = v.UnicodeString(strip=True, min=1, not_empty=False)
        private = v.StringBoolean(if_missing=False)
        enable_statistics = v.StringBoolean(if_missing=False)
        enable_downloads = v.StringBoolean(if_missing=False)
        landing_rev = v.OneOf(landing_revs, hideList=True)

        if edit:
            #this is repo owner
            user = All(v.UnicodeString(not_empty=True), v.ValidRepoUser())

        chained_validators = [v.ValidCloneUri(),
                              v.ValidRepoName(edit, old_data),
                              v.ValidPerms()]
    return _RepoForm


def RepoForkForm(edit=False, old_data={}, supported_backends=BACKENDS.keys(),
                 repo_groups=[]):
    class _RepoForkForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                        v.SlugifyName())
        repo_group = v.OneOf(repo_groups, hideList=True)
        repo_type = All(v.ValidForkType(old_data), v.OneOf(supported_backends))
        description = v.UnicodeString(strip=True, min=1, not_empty=True)
        private = v.StringBoolean(if_missing=False)
        copy_permissions = v.StringBoolean(if_missing=False)
        update_after_clone = v.StringBoolean(if_missing=False)
        fork_parent_id = v.UnicodeString()
        chained_validators = [v.ValidForkName(edit, old_data)]

    return _RepoForkForm


def RepoSettingsForm(edit=False, old_data={},
                     supported_backends=BACKENDS.keys(), repo_groups=[],
                     landing_revs=[]):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                        v.SlugifyName())
        description = v.UnicodeString(strip=True, min=1, not_empty=True)
        repo_group = v.OneOf(repo_groups, hideList=True)
        private = v.StringBoolean(if_missing=False)
        landing_rev = v.OneOf(landing_revs, hideList=True)
        chained_validators = [v.ValidRepoName(edit, old_data), v.ValidPerms(),
                              v.ValidSettings()]
    return _RepoForm


def ApplicationSettingsForm():
    class _ApplicationSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        rhodecode_title = v.UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_realm = v.UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_ga_code = v.UnicodeString(strip=True, min=1, not_empty=False)

    return _ApplicationSettingsForm


def ApplicationUiSettingsForm():
    class _ApplicationUiSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        web_push_ssl = v.OneOf(['true', 'false'], if_missing='false')
        paths_root_path = All(
            v.ValidPath(),
            v.UnicodeString(strip=True, min=1, not_empty=True)
        )
        hooks_changegroup_update = v.OneOf(['True', 'False'],
                                           if_missing=False)
        hooks_changegroup_repo_size = v.OneOf(['True', 'False'],
                                              if_missing=False)
        hooks_changegroup_push_logger = v.OneOf(['True', 'False'],
                                                if_missing=False)
        hooks_preoutgoing_pull_logger = v.OneOf(['True', 'False'],
                                                if_missing=False)

    return _ApplicationUiSettingsForm


def DefaultPermissionsForm(perms_choices, register_choices, create_choices):
    class _DefaultPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        overwrite_default = v.StringBoolean(if_missing=False)
        anonymous = v.OneOf(['True', 'False'], if_missing=False)
        default_perm = v.OneOf(perms_choices)
        default_register = v.OneOf(register_choices)
        default_create = v.OneOf(create_choices)

    return _DefaultPermissionsForm


def LdapSettingsForm(tls_reqcert_choices, search_scope_choices,
                     tls_kind_choices):
    class _LdapSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        #pre_validators = [LdapLibValidator]
        ldap_active = v.StringBoolean(if_missing=False)
        ldap_host = v.UnicodeString(strip=True,)
        ldap_port = v.Number(strip=True,)
        ldap_tls_kind = v.OneOf(tls_kind_choices)
        ldap_tls_reqcert = v.OneOf(tls_reqcert_choices)
        ldap_dn_user = v.UnicodeString(strip=True,)
        ldap_dn_pass = v.UnicodeString(strip=True,)
        ldap_base_dn = v.UnicodeString(strip=True,)
        ldap_filter = v.UnicodeString(strip=True,)
        ldap_search_scope = v.OneOf(search_scope_choices)
        ldap_attr_login = All(
            v.AttrLoginValidator(),
            v.UnicodeString(strip=True,)
        )
        ldap_attr_firstname = v.UnicodeString(strip=True,)
        ldap_attr_lastname = v.UnicodeString(strip=True,)
        ldap_attr_email = v.UnicodeString(strip=True,)

    return _LdapSettingsForm
