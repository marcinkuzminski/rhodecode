# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.ldap_settings
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    ldap controller for RhodeCode
    
    :created_on: Nov 26, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
import logging
import formencode
import traceback

from formencode import htmlfill

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.lib.base import BaseController, render
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.auth_ldap import LdapImportError
from rhodecode.model.settings import SettingsModel
from rhodecode.model.forms import LdapSettingsForm
from sqlalchemy.exc import DatabaseError

log = logging.getLogger(__name__)



class LdapSettingsController(BaseController):

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(LdapSettingsController, self).__before__()

    def index(self):
        defaults = SettingsModel().get_ldap_settings()

        return htmlfill.render(
                    render('admin/ldap/ldap.html'),
                    defaults=defaults,
                    encoding="UTF-8",
                    force_defaults=True,)

    def ldap_settings(self):
        """POST ldap create and store ldap settings"""

        settings_model = SettingsModel()
        _form = LdapSettingsForm()()

        try:
            form_result = _form.to_python(dict(request.POST))
            try:

                for k, v in form_result.items():
                    if k.startswith('ldap_'):
                        setting = settings_model.get(k)
                        setting.app_settings_value = v
                        self.sa.add(setting)

                self.sa.commit()
                h.flash(_('Ldap settings updated successfully'),
                    category='success')
            except (DatabaseError,):
                raise
        except LdapImportError:
            h.flash(_('Unable to activate ldap. The "python-ldap" library '
                      'is missing.'), category='warning')

        except formencode.Invalid, errors:

            return htmlfill.render(
                render('admin/ldap/ldap.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of ldap settings'),
                    category='error')

        return redirect(url('ldap_home'))
