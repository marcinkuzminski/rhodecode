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
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator,\
    AuthUser
from rhodecode.lib.base import BaseController, render
from rhodecode.model.forms import DefaultPermissionsForm
from rhodecode.model.permission import PermissionModel
from rhodecode.model.db import User, UserIpMap, Permission
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
        super(PermissionsController, self).__before__()

        c.repo_perms_choices = [('repository.none', _('None'),),
                                   ('repository.read', _('Read'),),
                                   ('repository.write', _('Write'),),
                                   ('repository.admin', _('Admin'),)]
        c.group_perms_choices = [('group.none', _('None'),),
                                 ('group.read', _('Read'),),
                                 ('group.write', _('Write'),),
                                 ('group.admin', _('Admin'),)]
        c.user_group_perms_choices = [('usergroup.none', _('None'),),
                                      ('usergroup.read', _('Read'),),
                                      ('usergroup.write', _('Write'),),
                                      ('usergroup.admin', _('Admin'),)]
        c.register_choices = [
            ('hg.register.none',
                _('Disabled')),
            ('hg.register.manual_activate',
                _('Allowed with manual account activation')),
            ('hg.register.auto_activate',
                _('Allowed with automatic account activation')), ]

        c.extern_activate_choices = [
            ('hg.extern_activate.manual', _('Manual activation of external account')),
            ('hg.extern_activate.auto', _('Automatic activation of external account')),
        ]

        c.repo_create_choices = [('hg.create.none', _('Disabled')),
                                 ('hg.create.repository', _('Enabled'))]

        c.user_group_create_choices = [('hg.usergroup.create.false', _('Disabled')),
                                       ('hg.usergroup.create.true', _('Enabled'))]

        c.repo_group_create_choices = [('hg.repogroup.create.false', _('Disabled')),
                                       ('hg.repogroup.create.true', _('Enabled'))]

        c.fork_choices = [('hg.fork.none', _('Disabled')),
                          ('hg.fork.repository', _('Enabled'))]

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
        if id == 'default':
            c.user = default_user = User.get_default_user()
            c.perm_user = AuthUser(user_id=default_user.user_id)
            c.user_ip_map = UserIpMap.query()\
                            .filter(UserIpMap.user == default_user).all()

            _form = DefaultPermissionsForm(
                    [x[0] for x in c.repo_perms_choices],
                    [x[0] for x in c.group_perms_choices],
                    [x[0] for x in c.user_group_perms_choices],
                    [x[0] for x in c.repo_create_choices],
                    [x[0] for x in c.repo_group_create_choices],
                    [x[0] for x in c.user_group_create_choices],
                    [x[0] for x in c.fork_choices],
                    [x[0] for x in c.register_choices],
                    [x[0] for x in c.extern_activate_choices],
            )()

            try:
                form_result = _form.to_python(dict(request.POST))
                form_result.update({'perm_user_name': id})
                PermissionModel().update(form_result)
                Session().commit()
                h.flash(_('Default permissions updated successfully'),
                        category='success')

            except formencode.Invalid, errors:
                defaults = errors.value

                return htmlfill.render(
                    render('admin/permissions/permissions.html'),
                    defaults=defaults,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")
            except Exception:
                log.error(traceback.format_exc())
                h.flash(_('Error occurred during update of permissions'),
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
        Permission.get_or_404(-1)

    def edit(self, id, format='html'):
        """GET /permissions/id/edit: Form to edit an existing item"""
        #url('edit_permission', id=ID)

        #this form can only edit default user permissions
        if id == 'default':
            c.user = User.get_default_user()
            defaults = {'anonymous': c.user.active}
            c.perm_user = c.user.AuthUser
            c.user_ip_map = UserIpMap.query()\
                            .filter(UserIpMap.user == c.user).all()
            for p in c.user.user_perms:
                if p.permission.permission_name.startswith('repository.'):
                    defaults['default_repo_perm'] = p.permission.permission_name

                if p.permission.permission_name.startswith('group.'):
                    defaults['default_group_perm'] = p.permission.permission_name

                if p.permission.permission_name.startswith('usergroup.'):
                    defaults['default_user_group_perm'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.create.'):
                    defaults['default_repo_create'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.repogroup.'):
                    defaults['default_repo_group_create'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.usergroup.'):
                    defaults['default_user_group_create'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.register.'):
                    defaults['default_register'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.extern_activate.'):
                    defaults['default_extern_activate'] = p.permission.permission_name

                if p.permission.permission_name.startswith('hg.fork.'):
                    defaults['default_fork'] = p.permission.permission_name

            return htmlfill.render(
                render('admin/permissions/permissions.html'),
                defaults=defaults,
                encoding="UTF-8",
                force_defaults=False
            )
        else:
            return redirect(url('admin_home'))
