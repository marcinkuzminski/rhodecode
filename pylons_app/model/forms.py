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
from formencode.validators import UnicodeString, OneOf, Int, Number, Regex
from pylons import session
from pylons.i18n.translation import _
from pylons_app.lib.auth import get_crypt_password
from pylons_app.model import meta
from pylons_app.model.db import User
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from webhelpers.pylonslib.secure_form import authentication_token
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
        if user:
            if user.active:
                if user.username == username and user.password == crypted_passwd:
                    from pylons_app.lib.auth import AuthUser
                    auth_user = AuthUser()
                    auth_user.username = username
                    auth_user.is_authenticated = True
                    auth_user.is_admin = user.admin
                    session['hg_app_user'] = auth_user
                    session.save()
                    log.info('user %s is now authenticated', username)
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
    

