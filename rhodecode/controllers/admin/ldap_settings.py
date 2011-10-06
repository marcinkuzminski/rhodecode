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
import logging
import formencode
import traceback

from formencode import htmlfill

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from sqlalchemy.exc import DatabaseError

from rhodecode.lib.base import BaseController, render
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.exceptions import LdapImportError
from rhodecode.model.forms import LdapSettingsForm
from rhodecode.model.db import RhodeCodeSettings

log = logging.getLogger(__name__)


class LdapSettingsController(BaseController):

    search_scope_choices = [('BASE', _('BASE'),),
                            ('ONELEVEL', _('ONELEVEL'),),
                            ('SUBTREE', _('SUBTREE'),),
                            ]
    search_scope_default = 'SUBTREE'

    tls_reqcert_choices = [('NEVER', _('NEVER'),),
                           ('ALLOW', _('ALLOW'),),
                           ('TRY', _('TRY'),),
                           ('DEMAND', _('DEMAND'),),
                           ('HARD', _('HARD'),),
                           ]
    tls_reqcert_default = 'DEMAND'

    tls_kind_choices = [('PLAIN', _('No encryption'),),
                        ('LDAPS', _('LDAPS connection'),),
                        ('START_TLS', _('START_TLS on LDAP connection'),)
                        ]

    tls_kind_default = 'PLAIN'

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        c.search_scope_choices = self.search_scope_choices
        c.tls_reqcert_choices = self.tls_reqcert_choices
        c.tls_kind_choices = self.tls_kind_choices

        c.search_scope_cur = self.search_scope_default
        c.tls_reqcert_cur = self.tls_reqcert_default
        c.tls_kind_cur = self.tls_kind_default

        super(LdapSettingsController, self).__before__()

    def index(self):
        defaults = RhodeCodeSettings.get_ldap_settings()
        c.search_scope_cur = defaults.get('ldap_search_scope')
        c.tls_reqcert_cur = defaults.get('ldap_tls_reqcert')
        c.tls_kind_cur = defaults.get('ldap_tls_kind')

        return htmlfill.render(
                    render('admin/ldap/ldap.html'),
                    defaults=defaults,
                    encoding="UTF-8",
                    force_defaults=True,)

    def ldap_settings(self):
        """POST ldap create and store ldap settings"""

        _form = LdapSettingsForm([x[0] for x in self.tls_reqcert_choices],
                                 [x[0] for x in self.search_scope_choices],
                                 [x[0] for x in self.tls_kind_choices])()

        try:
            form_result = _form.to_python(dict(request.POST))
            try:

                for k, v in form_result.items():
                    if k.startswith('ldap_'):
                        setting = RhodeCodeSettings.get_by_name(k)
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
            e = errors.error_dict or {}

            return htmlfill.render(
                render('admin/ldap/ldap.html'),
                defaults=errors.value,
                errors=e,
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of ldap settings'),
                    category='error')

        return redirect(url('ldap_home'))
