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
from formencode import All
from formencode.validators import UnicodeString, OneOf, Int, Number, Regex, \
    Email, Bool, StringBoolean
from pylons import session
from pylons.i18n.translation import _
from pylons_app.lib.auth import check_password, get_crypt_password
from pylons_app.model import meta
from pylons_app.model.user_model import UserModel
from pylons_app.model.db import User, Repository
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from webhelpers.pylonslib.secure_form import authentication_token
import formencode
import logging
import os
import pylons_app.lib.helpers as h
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
            #check if user is uniq
            sa = meta.Session
            old_un = None
            if edit:
                old_un = sa.query(User).get(old_data.get('user_id')).username
                
            if old_un != value or not edit:    
                if sa.query(User).filter(User.username == value).scalar():
                    raise formencode.Invalid(_('This username already exists') ,
                                             value, state)
            meta.Session.remove()
                            
    return _ValidUsername   
    
class ValidPassword(formencode.validators.FancyValidator):
    
    def to_python(self, value, state):
        if value:
            return get_crypt_password(value)
        
class ValidAuth(formencode.validators.FancyValidator):
    messages = {
            'invalid_password':_('invalid password'),
            'invalid_login':_('invalid user name'),
            'disabled_account':_('Your acccount is disabled')
            
            }
    #error mapping
    e_dict = {'username':messages['invalid_login'],
              'password':messages['invalid_password']}
    e_dict_disable = {'username':messages['disabled_account']}
    
    def validate_python(self, value, state):
        password = value['password']
        username = value['username']
        user = UserModel().get_user_by_name(username)
        if user is None:
            raise formencode.Invalid(self.message('invalid_password',
                                     state=State_obj), value, state,
                                     error_dict=self.e_dict)            
        if user:
            if user.active:
                if user.username == username and check_password(password,
                                                                user.password):
                    return value
                else:
                    log.warning('user %s not authenticated', username)
                    raise formencode.Invalid(self.message('invalid_password',
                                             state=State_obj), value, state,
                                             error_dict=self.e_dict)
            else:
                log.warning('user %s is disabled', username)
                raise formencode.Invalid(self.message('disabled_account',
                                         state=State_obj),
                                         value, state,
                                         error_dict=self.e_dict_disable)
                   
class ValidRepoUser(formencode.validators.FancyValidator):
            
    def to_python(self, value, state):
        try:
            self.user_db = meta.Session.query(User)\
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
                sa = meta.Session
                if sa.query(Repository).filter(Repository.repo_name == slug).scalar():
                    raise formencode.Invalid(_('This repository already exists') ,
                                             value, state)
                meta.Session.remove()
            return slug 
        
        
    return _ValidRepoName

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
                raise formencode.Invalid(msg, value, state, error_dict={'perm_new_user_name':msg})            
        return value
    
class ValidSettings(formencode.validators.FancyValidator):
    
    def to_python(self, value, state):
        #settings  form can't edit user
        if value.has_key('user'):
            del['value']['user']
        
        return value
    
class ValidPath(formencode.validators.FancyValidator):
    def to_python(self, value, state):
        isdir = os.path.isdir(value.replace('*', ''))
        if (value.endswith('/*') or value.endswith('/**')) and isdir:
            return value
        elif not isdir:
            msg = _('This is not a valid path') 
        else:
            msg = _('You need to specify * or ** at the end of path (ie. /tmp/*)')
        
        raise formencode.Invalid(msg, value, state,
                                     error_dict={'paths_root_path':msg})            

def UniqSystemEmail(old_data):
    class _UniqSystemEmail(formencode.validators.FancyValidator):
        def to_python(self, value, state):
            if old_data.get('email') != value:
                sa = meta.Session
                try:
                    user = sa.query(User).filter(User.email == value).scalar()
                    if user:
                        raise formencode.Invalid(_("That e-mail address is already taken") ,
                                                 value, state)
                finally:
                    meta.Session.remove()
                
            return value
        
    return _UniqSystemEmail
    
class ValidSystemEmail(formencode.validators.FancyValidator):
    def to_python(self, value, state):
        sa = meta.Session
        try:
            user = sa.query(User).filter(User.email == value).scalar()
            if  user is None:
                raise formencode.Invalid(_("That e-mail address doesn't exist.") ,
                                         value, state)
        finally:
            meta.Session.remove()
            
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
                                      'tooShort':_('Enter a value %(min)i characters long or more')}
                                )


    #chained validators have access to all data
    chained_validators = [ValidAuth]
    
def UserForm(edit=False, old_data={}):
    class _UserForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(UnicodeString(strip=True, min=1, not_empty=True), ValidUsername(edit, old_data))
        if edit:
            new_password = All(UnicodeString(strip=True, min=6, not_empty=False), ValidPassword)
            admin = StringBoolean(if_missing=False)
        else:
            password = All(UnicodeString(strip=True, min=6, not_empty=True), ValidPassword)
        active = StringBoolean(if_missing=False)
        name = UnicodeString(strip=True, min=1, not_empty=True)
        lastname = UnicodeString(strip=True, min=1, not_empty=True)
        email = All(Email(not_empty=True), UniqSystemEmail(old_data))
        
    return _UserForm

RegisterForm = UserForm

def PasswordResetForm():
    class _PasswordResetForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        email = All(ValidSystemEmail(), Email(not_empty=True))             
    return _PasswordResetForm

def RepoForm(edit=False, old_data={}):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True), ValidRepoName(edit, old_data))
        description = UnicodeString(strip=True, min=1, not_empty=True)
        private = StringBoolean(if_missing=False)
        
        if edit:
            user = All(Int(not_empty=True), ValidRepoUser)
        
        chained_validators = [ValidPerms]
    return _RepoForm

def RepoSettingsForm(edit=False, old_data={}):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True), ValidRepoName(edit, old_data))
        description = UnicodeString(strip=True, min=1, not_empty=True)
        private = StringBoolean(if_missing=False)
        
        chained_validators = [ValidPerms, ValidSettings]
    return _RepoForm


def ApplicationSettingsForm():
    class _ApplicationSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        hg_app_title = UnicodeString(strip=True, min=1, not_empty=True)
        hg_app_realm = UnicodeString(strip=True, min=1, not_empty=True)
        
    return _ApplicationSettingsForm
 
def ApplicationUiSettingsForm():
    class _ApplicationUiSettingsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        web_push_ssl = OneOf(['true', 'false'], if_missing='false')
        paths_root_path = All(ValidPath(), UnicodeString(strip=True, min=1, not_empty=True))
        hooks_changegroup_update = OneOf(['True', 'False'], if_missing=False)
        hooks_changegroup_repo_size = OneOf(['True', 'False'], if_missing=False)
        
    return _ApplicationUiSettingsForm

def DefaultPermissionsForm(perms_choices, register_choices, create_choices):
    class _DefaultPermissionsForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        overwrite_default = OneOf(['true', 'false'], if_missing='false')
        default_perm = OneOf(perms_choices)
        default_register = OneOf(register_choices)
        default_create = OneOf(create_choices)
        
    return _DefaultPermissionsForm
