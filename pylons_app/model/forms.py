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
for select use formencode.All(OneOf(list), Int())
    
"""

import formencode
from formencode.validators import UnicodeString, OneOf, Int, Number, Regex
from pylons.i18n.translation import _
from webhelpers.pylonslib.secure_form import authentication_token

class ValidAuthToken(formencode.validators.FancyValidator):
    messages = {'invalid_token':_('Token mismatch')}

    def validate_python(self, value, state):

        if value != authentication_token():
            raise formencode.Invalid(self.message('invalid_token', state, search_number=value), value, state)


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


