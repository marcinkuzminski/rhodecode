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
                v.ValidPassword(),
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
        firstname = v.UnicodeString(strip=True, min=1, not_empty=False)
        lastname = v.UnicodeString(strip=True, min=1, not_empty=False)
        email = All(v.Email(not_empty=True), v.UniqSystemEmail(old_data))

        chained_validators = [v.ValidPasswordsMatch()]

    return _UserForm


def UserGroupForm(edit=False, old_data={}, available_members=[]):
    class _UserGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        users_group_name = All(
            v.UnicodeString(strip=True, min=1, not_empty=True),
            v.ValidUserGroup(edit, old_data)
        )

        users_group_active = v.StringBoolean(if_missing=False)

        if edit:
            users_group_members = v.OneOf(
                available_members, hideList=False, testValueList=True,
                if_missing=None, not_empty=False
            )

    return _UserGroupForm


def ReposGroupForm(edit=False, old_data={}, available_groups=[],
                   can_create_in_root=False):
    class _ReposGroupForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False

        group_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                               v.SlugifyName())
        group_description = v.UnicodeString(strip=True, min=1,
                                                not_empty=False)
        if edit:
            #FIXME: do a special check that we cannot move a group to one of
            #it's children
            pass
        group_parent_id = All(v.CanCreateGroup(can_create_in_root),
                              v.OneOf(available_groups, hideList=False,
                                      testValueList=True,
                                      if_missing=None, not_empty=True))
        enable_locking = v.StringBoolean(if_missing=False)
        chained_validators = [v.ValidReposGroup(edit, old_data)]

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
        firstname = v.UnicodeString(strip=True, min=1, not_empty=False)
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
        repo_group = All(v.CanWriteGroup(old_data),
                         v.OneOf(repo_groups, hideList=True))
        repo_type = v.OneOf(supported_backends, required=False,
                            if_missing=old_data.get('repo_type'))
        repo_description = v.UnicodeString(strip=True, min=1, not_empty=False)
        repo_private = v.StringBoolean(if_missing=False)
        repo_landing_rev = v.OneOf(landing_revs, hideList=True)
        clone_uri = All(v.UnicodeString(strip=True, min=1, not_empty=False))

        repo_enable_statistics = v.StringBoolean(if_missing=False)
        repo_enable_downloads = v.StringBoolean(if_missing=False)
        repo_enable_locking = v.StringBoolean(if_missing=False)

        if edit:
            #this is repo owner
            user = All(v.UnicodeString(not_empty=True), v.ValidRepoUser())

        chained_validators = [v.ValidCloneUri(),
                              v.ValidRepoName(edit, old_data)]
    return _RepoForm


def RepoPermsForm():
    class _RepoPermsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        chained_validators = [v.ValidPerms(type_='repo')]
    return _RepoPermsForm


def RepoGroupPermsForm():
    class _RepoGroupPermsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        recursive = v.StringBoolean(if_missing=False)
        chained_validators = [v.ValidPerms(type_='repo_group')]
    return _RepoGroupPermsForm


def UserGroupPermsForm():
    class _UserPermsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        chained_validators = [v.ValidPerms(type_='user_group')]
    return _UserPermsForm


def RepoFieldForm():
    class _RepoFieldForm(formencode.Schema):
        filter_extra_fields = True
        allow_extra_fields = True

        new_field_key = All(v.FieldKey(),
                            v.UnicodeString(strip=True, min=3, not_empty=True))
        new_field_value = v.UnicodeString(not_empty=False, if_missing='')
        new_field_type = v.OneOf(['str', 'unicode', 'list', 'tuple'],
                                 if_missing='str')
        new_field_label = v.UnicodeString(not_empty=False)
        new_field_desc = v.UnicodeString(not_empty=False)

    return _RepoFieldForm


def RepoForkForm(edit=False, old_data={}, supported_backends=BACKENDS.keys(),
                 repo_groups=[], landing_revs=[]):
    class _RepoForkForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(v.UnicodeString(strip=True, min=1, not_empty=True),
                        v.SlugifyName())
        repo_group = All(v.CanWriteGroup(),
                         v.OneOf(repo_groups, hideList=True))
        repo_type = All(v.ValidForkType(old_data), v.OneOf(supported_backends))
        description = v.UnicodeString(strip=True, min=1, not_empty=True)
        private = v.StringBoolean(if_missing=False)
        copy_permissions = v.StringBoolean(if_missing=False)
        update_after_clone = v.StringBoolean(if_missing=False)
        fork_parent_id = v.UnicodeString()
        chained_validators = [v.ValidForkName(edit, old_data)]
        landing_rev = v.OneOf(landing_revs, hideList=True)

    return _RepoForkForm


def ApplicationSettingsForm():
    class _ApplicationSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        rhodecode_title = v.UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_realm = v.UnicodeString(strip=True, min=1, not_empty=True)
        rhodecode_ga_code = v.UnicodeString(strip=True, min=1, not_empty=False)

    return _ApplicationSettingsForm


def ApplicationVisualisationForm():
    class _ApplicationVisualisationForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        rhodecode_show_public_icon = v.StringBoolean(if_missing=False)
        rhodecode_show_private_icon = v.StringBoolean(if_missing=False)
        rhodecode_stylify_metatags = v.StringBoolean(if_missing=False)

        rhodecode_repository_fields = v.StringBoolean(if_missing=False)
        rhodecode_lightweight_journal = v.StringBoolean(if_missing=False)
        rhodecode_dashboard_items = v.Int(min=5, not_empty=True)
        rhodecode_show_version = v.StringBoolean(if_missing=False)

    return _ApplicationVisualisationForm


def ApplicationUiSettingsForm():
    class _ApplicationUiSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        web_push_ssl = v.StringBoolean(if_missing=False)
        paths_root_path = All(
            v.ValidPath(),
            v.UnicodeString(strip=True, min=1, not_empty=True)
        )
        hooks_changegroup_update = v.StringBoolean(if_missing=False)
        hooks_changegroup_repo_size = v.StringBoolean(if_missing=False)
        hooks_changegroup_push_logger = v.StringBoolean(if_missing=False)
        hooks_outgoing_pull_logger = v.StringBoolean(if_missing=False)

        extensions_largefiles = v.StringBoolean(if_missing=False)
        extensions_hgsubversion = v.StringBoolean(if_missing=False)
        extensions_hggit = v.StringBoolean(if_missing=False)

    return _ApplicationUiSettingsForm


def DefaultPermissionsForm(repo_perms_choices, group_perms_choices,
                           user_group_perms_choices, create_choices,
                           repo_group_create_choices, user_group_create_choices,
                           fork_choices, register_choices, extern_activate_choices):
    class _DefaultPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        overwrite_default_repo = v.StringBoolean(if_missing=False)
        overwrite_default_group = v.StringBoolean(if_missing=False)
        overwrite_default_user_group = v.StringBoolean(if_missing=False)
        anonymous = v.StringBoolean(if_missing=False)
        default_repo_perm = v.OneOf(repo_perms_choices)
        default_group_perm = v.OneOf(group_perms_choices)
        default_user_group_perm = v.OneOf(user_group_perms_choices)

        default_repo_create = v.OneOf(create_choices)
        default_user_group_create = v.OneOf(user_group_create_choices)
        #default_repo_group_create = v.OneOf(repo_group_create_choices) #not impl. yet
        default_fork = v.OneOf(fork_choices)

        default_register = v.OneOf(register_choices)
        default_extern_activate = v.OneOf(extern_activate_choices)
    return _DefaultPermissionsForm


def CustomDefaultPermissionsForm():
    class _CustomDefaultPermissionsForm(formencode.Schema):
        filter_extra_fields = True
        allow_extra_fields = True
        inherit_default_permissions = v.StringBoolean(if_missing=False)

        create_repo_perm = v.StringBoolean(if_missing=False)
        create_user_group_perm = v.StringBoolean(if_missing=False)
        #create_repo_group_perm Impl. later

        fork_repo_perm = v.StringBoolean(if_missing=False)

    return _CustomDefaultPermissionsForm


def DefaultsForm(edit=False, old_data={}, supported_backends=BACKENDS.keys()):
    class _DefaultsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        default_repo_type = v.OneOf(supported_backends)
        default_repo_private = v.StringBoolean(if_missing=False)
        default_repo_enable_statistics = v.StringBoolean(if_missing=False)
        default_repo_enable_downloads = v.StringBoolean(if_missing=False)
        default_repo_enable_locking = v.StringBoolean(if_missing=False)

    return _DefaultsForm


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
        ldap_attr_login = v.AttrLoginValidator()(not_empty=True)
        ldap_attr_firstname = v.UnicodeString(strip=True,)
        ldap_attr_lastname = v.UnicodeString(strip=True,)
        ldap_attr_email = v.UnicodeString(strip=True,)

    return _LdapSettingsForm


def UserExtraEmailForm():
    class _UserExtraEmailForm(formencode.Schema):
        email = All(v.UniqSystemEmail(), v.Email(not_empty=True))
    return _UserExtraEmailForm


def UserExtraIpForm():
    class _UserExtraIpForm(formencode.Schema):
        ip = v.ValidIp()(not_empty=True)
    return _UserExtraIpForm


def PullRequestForm(repo_id):
    class _PullRequestForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True

        user = v.UnicodeString(strip=True, required=True)
        org_repo = v.UnicodeString(strip=True, required=True)
        org_ref = v.UnicodeString(strip=True, required=True)
        other_repo = v.UnicodeString(strip=True, required=True)
        other_ref = v.UnicodeString(strip=True, required=True)
        revisions = All(#v.NotReviewedRevisions(repo_id)(),
                        v.UniqueList(not_empty=True))
        review_members = v.UniqueList(not_empty=True)

        pullrequest_title = v.UnicodeString(strip=True, required=True)
        pullrequest_desc = v.UnicodeString(strip=True, required=False)

        ancestor_rev = v.UnicodeString(strip=True, required=True)
        merge_rev = v.UnicodeString(strip=True, required=True)

    return _PullRequestForm


def GistForm(lifetime_options):
    class _GistForm(formencode.Schema):

        filename = All(v.BasePath()(),
                       v.UnicodeString(strip=True, required=False))
        description = v.UnicodeString(required=False, if_missing='')
        lifetime = v.OneOf(lifetime_options)
        mimetype = v.UnicodeString(required=False, if_missing=None)
        content = v.UnicodeString(required=True, not_empty=True)
        public = v.UnicodeString(required=False, if_missing='')
        private = v.UnicodeString(required=False, if_missing='')

    return _GistForm
