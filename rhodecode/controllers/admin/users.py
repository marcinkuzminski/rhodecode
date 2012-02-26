# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.users
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Users crud controller for pylons

    :created_on: Apr 4, 2010
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
from pylons import request, session, tmpl_context as c, url, config
from pylons.controllers.util import redirect
from pylons.i18n.translation import _

from rhodecode.lib.exceptions import DefaultUserException, \
    UserOwnsReposException
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.base import BaseController, render

from rhodecode.model.db import User, Permission
from rhodecode.model.forms import UserForm
from rhodecode.model.user import UserModel
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


class UsersController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('user', 'users')

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(UsersController, self).__before__()
        c.available_permissions = config['available_permissions']

    def index(self, format='html'):
        """GET /users: All items in the collection"""
        # url('users')

        c.users_list = self.sa.query(User).all()
        return render('admin/users/users.html')

    def create(self):
        """POST /users: Create a new item"""
        # url('users')

        user_model = UserModel()
        user_form = UserForm()()
        try:
            form_result = user_form.to_python(dict(request.POST))
            user_model.create(form_result)
            h.flash(_('created user %s') % form_result['username'],
                    category='success')
            Session.commit()
            #action_logger(self.rhodecode_user, 'new_user', '', '', self.sa)
        except formencode.Invalid, errors:
            return htmlfill.render(
                render('admin/users/user_add.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during creation of user %s') \
                    % request.POST.get('username'), category='error')
        return redirect(url('users'))

    def new(self, format='html'):
        """GET /users/new: Form to create a new item"""
        # url('new_user')
        return render('admin/users/user_add.html')

    def update(self, id):
        """PUT /users/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('update_user', id=ID),
        #           method='put')
        # url('user', id=ID)
        user_model = UserModel()
        c.user = user_model.get(id)

        _form = UserForm(edit=True, old_data={'user_id': id,
                                              'email': c.user.email})()
        form_result = {}
        try:
            form_result = _form.to_python(dict(request.POST))
            user_model.update(id, form_result)
            h.flash(_('User updated successfully'), category='success')
            Session.commit()
        except formencode.Invalid, errors:
            e = errors.error_dict or {}
            perm = Permission.get_by_key('hg.create.repository')
            e.update({'create_repo_perm': user_model.has_perm(id, perm)})
            return htmlfill.render(
                render('admin/users/user_edit.html'),
                defaults=errors.value,
                errors=e,
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occurred during update of user %s') \
                    % form_result.get('username'), category='error')

        return redirect(url('users'))

    def delete(self, id):
        """DELETE /users/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('delete_user', id=ID),
        #           method='delete')
        # url('user', id=ID)
        user_model = UserModel()
        try:
            user_model.delete(id)
            h.flash(_('successfully deleted user'), category='success')
            Session.commit()
        except (UserOwnsReposException, DefaultUserException), e:
            h.flash(str(e), category='warning')
        except Exception:
            h.flash(_('An error occurred during deletion of user'),
                    category='error')
        return redirect(url('users'))

    def show(self, id, format='html'):
        """GET /users/id: Show a specific item"""
        # url('user', id=ID)

    def edit(self, id, format='html'):
        """GET /users/id/edit: Form to edit an existing item"""
        # url('edit_user', id=ID)
        c.user = User.get(id)
        if not c.user:
            return redirect(url('users'))
        if c.user.username == 'default':
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(url('users'))
        c.user.permissions = {}
        c.granted_permissions = UserModel().fill_perms(c.user)\
            .permissions['global']

        defaults = c.user.get_dict()
        perm = Permission.get_by_key('hg.create.repository')
        defaults.update({'create_repo_perm': UserModel().has_perm(id, perm)})

        return htmlfill.render(
            render('admin/users/user_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    def update_perm(self, id):
        """PUT /users_perm/id: Update an existing item"""
        # url('user_perm', id=ID, method='put')

        grant_perm = request.POST.get('create_repo_perm', False)
        user_model = UserModel()

        if grant_perm:
            perm = Permission.get_by_key('hg.create.none')
            user_model.revoke_perm(id, perm)

            perm = Permission.get_by_key('hg.create.repository')
            user_model.grant_perm(id, perm)
            h.flash(_("Granted 'repository create' permission to user"),
                    category='success')
            Session.commit()
        else:
            perm = Permission.get_by_key('hg.create.repository')
            user_model.revoke_perm(id, perm)

            perm = Permission.get_by_key('hg.create.none')
            user_model.grant_perm(id, perm)
            h.flash(_("Revoked 'repository create' permission to user"),
                    category='success')
            Session.commit()
        return redirect(url('edit_user', id=id))
