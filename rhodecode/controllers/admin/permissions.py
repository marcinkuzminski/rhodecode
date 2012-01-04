# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.permissions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    permissions controller for Rhodecode

    :created_on: Apr 27, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
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
import traceback
import formencode
from formencode import htmlfill

from pylons import request, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.model.forms import DefaultPermissionsForm
from rhodecode.model.permission import PermissionModel
from rhodecode.model.db import User
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class PermissionsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('permission', 'permissions')

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(PermissionsController, self).__before__()

        self.perms_choices = [('repository.none', _('None'),),
                              ('repository.read', _('Read'),),
                              ('repository.write', _('Write'),),
                              ('repository.admin', _('Admin'),)]
        self.register_choices = [
            ('hg.register.none',
                _('disabled')),
            ('hg.register.manual_activate',
                _('allowed with manual account activation')),
            ('hg.register.auto_activate',
                _('allowed with automatic account activation')), ]

        self.create_choices = [('hg.create.none', _('Disabled')),
                               ('hg.create.repository', _('Enabled'))]

    def index(self, format='html'):
        """GET /permissions: All items in the collection"""
        # url('permissions')

    def create(self):
        """POST /permissions: Create a new item"""
        # url('permissions')

    def new(self, format='html'):
        """GET /permissions/new: Form to create a new item"""
        # url('new_permission')

    def update(self, id):
        """PUT /permissions/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('permission', id=ID),
        #           method='put')
        # url('permission', id=ID)

        permission_model = PermissionModel()

        _form = DefaultPermissionsForm([x[0] for x in self.perms_choices],
                                       [x[0] for x in self.register_choices],
                                       [x[0] for x in self.create_choices])()

        try:
            form_result = _form.to_python(dict(request.POST))
            form_result.update({'perm_user_name': id})
            permission_model.update(form_result)
            Session.commit()
            h.flash(_('Default permissions updated successfully'),
                    category='success')

        except formencode.Invalid, errors:
            c.perms_choices = self.perms_choices
            c.register_choices = self.register_choices
            c.create_choices = self.create_choices
            defaults = errors.value

            return htmlfill.render(
                render('admin/permissions/permissions.html'),
                defaults=defaults,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of permissions'),
                    category='error')

        return redirect(url('edit_permission', id=id))

    def delete(self, id):
        """DELETE /permissions/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('permission', id=ID),
        #           method='delete')
        # url('permission', id=ID)

    def show(self, id, format='html'):
        """GET /permissions/id: Show a specific item"""
        # url('permission', id=ID)

    def edit(self, id, format='html'):
        """GET /permissions/id/edit: Form to edit an existing item"""
        #url('edit_permission', id=ID)
        c.perms_choices = self.perms_choices
        c.register_choices = self.register_choices
        c.create_choices = self.create_choices

        if id == 'default':
            default_user = User.get_by_username('default')
            defaults = {'_method': 'put',
                        'anonymous': default_user.active}

            for p in default_user.user_perms:
                if p.permission.permission_name.startswith('repository.'):
                    defaults['default_perm'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.register.'):
                    defaults['default_register'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.create.'):
                    defaults['default_create'] = p.permission.permission_name

            return htmlfill.render(
                        render('admin/permissions/permissions.html'),
                        defaults=defaults,
                        encoding="UTF-8",
                        force_defaults=True,)
        else:
            return redirect(url('admin_home'))
