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
from pylons_app.lib.auth import get_crypt_password
import pylons_app.lib.helpers as h
from pylons_app.model import meta
from pylons_app.model.db import User, Repository
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from webhelpers.pylonslib.secure_form import authentication_token
import datetime
import formencode
import logging
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
class ValidUsername(formencode.validators.FancyValidator):

    def validate_python(self, value, state):
        if value in ['default', 'new_user']:
            raise formencode.Invalid(_('Invalid username'), value, state)
    
class ValidPassword(formencode.validators.FancyValidator):
    
    def to_python(self, value, state):
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
        sa = meta.Session
        crypted_passwd = get_crypt_password(value['password'])
        username = value['username']
        try:
            user = sa.query(User).filter(User.username == username).one()
        except (NoResultFound, MultipleResultsFound, OperationalError) as e:
            log.error(e)
            user = None
            raise formencode.Invalid(self.message('invalid_password',
                                     state=State_obj), value, state,
                                     error_dict=self.e_dict)            
        if user:
            if user.active:
                if user.username == username and user.password == crypted_passwd:
                    from pylons_app.lib.auth import AuthUser
                    auth_user = AuthUser()
                    auth_user.username = username
                    auth_user.is_authenticated = True
                    auth_user.is_admin = user.admin
                    auth_user.user_id = user.user_id
                    session['hg_app_user'] = auth_user
                    session.save()
                    log.info('user %s is now authenticated', username)
                    
                    try:
                        user.last_login = datetime.datetime.now()
                        sa.add(user)
                        sa.commit()                        
                    except (OperationalError) as e:
                        log.error(e)
                        sa.rollback()
                    
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
        sa = meta.Session
        try:
            self.user_db = sa.query(User)\
                .filter(User.active == True)\
                .filter(User.username == value).one()
        except Exception:
            raise formencode.Invalid(_('This username is not valid'),
                                     value, state)
        return self.user_db.user_id

def ValidRepoName(edit=False):    
    class _ValidRepoName(formencode.validators.FancyValidator):
            
        def to_python(self, value, state):
            slug = h.repo_name_slug(value)
            if slug in ['_admin']:
                raise formencode.Invalid(_('This repository name is disallowed'),
                                         value, state)
            sa = meta.Session
            if sa.query(Repository).get(slug) and not edit:
                raise formencode.Invalid(_('This repository already exists'),
                                         value, state)
                        
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
#===============================================================================
# FORMS        
#===============================================================================
class LoginForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    username = UnicodeString(
                             strip=True,
                             min=3,
                             not_empty=True,
                             messages={
                                       'empty':_('Please enter a login'),
                                       'tooShort':_('Enter a value %(min)i characters long or more')}
                            )

    password = UnicodeString(
                            strip=True,
                            min=3,
                            not_empty=True,
                            messages={
                                      'empty':_('Please enter a password'),
                                      'tooShort':_('Enter a value %(min)i characters long or more')}
                                )


    #chained validators have access to all data
    chained_validators = [ValidAuth]
    
def UserForm(edit=False):
    class _UserForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = True
        username = All(UnicodeString(strip=True, min=3, not_empty=True), ValidUsername)
        if edit:
            new_password = All(UnicodeString(strip=True, min=3, not_empty=False), ValidPassword)
            admin = StringBoolean(if_missing=False)
        else:
            password = All(UnicodeString(strip=True, min=3, not_empty=False), ValidPassword)
        active = StringBoolean(if_missing=False)
        name = UnicodeString(strip=True, min=3, not_empty=True)
        lastname = UnicodeString(strip=True, min=3, not_empty=True)
        email = Email(not_empty=True)
        
    return _UserForm

def RepoForm(edit=False):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True), ValidRepoName(edit))
        description = UnicodeString(strip=True, min=3, not_empty=True)
        private = StringBoolean(if_missing=False)
        
        if edit:
            user = All(Int(not_empty=True), ValidRepoUser)
        
        chained_validators = [ValidPerms]
    return _RepoForm

def RepoSettingsForm(edit=False):
    class _RepoForm(formencode.Schema):
        allow_extra_fields = True
        filter_extra_fields = False
        repo_name = All(UnicodeString(strip=True, min=1, not_empty=True), ValidRepoName(edit))
        description = UnicodeString(strip=True, min=3, not_empty=True)
        private = StringBoolean(if_missing=False)
        
        chained_validators = [ValidPerms, ValidSettings]
    return _RepoForm




