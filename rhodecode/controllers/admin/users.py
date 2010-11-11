#!/usr/bin/env python
# encoding: utf-8
# users controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
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
from rhodecode.lib.utils import action_logger
"""
Created on April 4, 2010
users controller for pylons
@author: marcink
"""

from formencode import htmlfill
from pylons import request, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from rhodecode.lib import helpers as h
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import User, UserLog
from rhodecode.model.forms import UserForm
from rhodecode.model.user import UserModel, DefaultUserException
import formencode
import logging
import traceback

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


    def index(self, format='html'):
        """GET /users: All items in the collection"""
        # url('users')

        c.users_list = self.sa.query(User).all()
        return render('admin/users/users.html')

    def create(self):
        """POST /users: Create a new item"""
        # url('users')

        user_model = UserModel()
        login_form = UserForm()()
        try:
            form_result = login_form.to_python(dict(request.POST))
            user_model.create(form_result)
            h.flash(_('created user %s') % form_result['username'],
                    category='success')
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
            h.flash(_('error occured during creation of user %s') \
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
        #    h.form(url('user', id=ID),
        #           method='put')
        # url('user', id=ID)
        user_model = UserModel()
        c.user = user_model.get(id)

        _form = UserForm(edit=True, old_data={'user_id':id,
                                              'email':c.user.email})()
        form_result = {}
        try:
            form_result = _form.to_python(dict(request.POST))
            user_model.update(id, form_result)
            h.flash(_('User updated succesfully'), category='success')

        except formencode.Invalid, errors:
            return htmlfill.render(
                render('admin/users/user_edit.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occured during update of user %s') \
                    % form_result.get('username'), category='error')

        return redirect(url('users'))

    def delete(self, id):
        """DELETE /users/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('user', id=ID),
        #           method='delete')
        # url('user', id=ID)
        user_model = UserModel()
        try:
            user_model.delete(id)
            h.flash(_('sucessfully deleted user'), category='success')
        except DefaultUserException, e:
            h.flash(str(e), category='warning')
        except Exception:
            h.flash(_('An error occured during deletion of user'),
                    category='error')
        return redirect(url('users'))

    def show(self, id, format='html'):
        """GET /users/id: Show a specific item"""
        # url('user', id=ID)


    def edit(self, id, format='html'):
        """GET /users/id/edit: Form to edit an existing item"""
        # url('edit_user', id=ID)
        c.user = self.sa.query(User).get(id)
        if not c.user:
            return redirect(url('users'))
        if c.user.username == 'default':
            h.flash(_("You can't edit this user"), category='warning')
            return redirect(url('users'))

        defaults = c.user.__dict__
        return htmlfill.render(
            render('admin/users/user_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
