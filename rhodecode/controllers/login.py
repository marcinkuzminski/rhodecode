# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.login
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Login controller for rhodeocode

    :created_on: Apr 22, 2010
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
import formencode

from formencode import htmlfill

from pylons.i18n.translation import _
from pylons.controllers.util import abort, redirect
from pylons import request, response, session, tmpl_context as c, url

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import AuthUser, HasPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import User
from rhodecode.model.forms import LoginForm, RegisterForm, PasswordResetForm
from rhodecode.model.user import UserModel
from rhodecode.model.meta import Session


log = logging.getLogger(__name__)


class LoginController(BaseController):

    def __before__(self):
        super(LoginController, self).__before__()

    def index(self):
        # redirect if already logged in
        c.came_from = request.GET.get('came_from', None)

        if self.rhodecode_user.is_authenticated \
                            and self.rhodecode_user.username != 'default':

            return redirect(url('home'))

        if request.POST:
            # import Login Form validator class
            login_form = LoginForm()
            try:
                c.form_result = login_form.to_python(dict(request.POST))
                # form checks for username/password, now we're authenticated
                username = c.form_result['username']
                user = User.get_by_username(username, case_insensitive=True)
                auth_user = AuthUser(user.user_id)
                auth_user.set_authenticated()
                cs = auth_user.get_cookie_store()
                session['rhodecode_user'] = cs
                # If they want to be remembered, update the cookie
                if c.form_result['remember'] is not False:
                    session.cookie_expires = False
                session._set_cookie_values()
                session._update_cookie_out()
                session.save()

                log.info('user %s is now authenticated and stored in '
                         'session, session attrs %s' % (username, cs))
                user.update_lastlogin()
                Session.commit()

                if c.came_from:
                    return redirect(c.came_from)
                else:
                    return redirect(url('home'))

            except formencode.Invalid, errors:
                return htmlfill.render(
                    render('/login.html'),
                    defaults=errors.value,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")

        return render('/login.html')

    @HasPermissionAnyDecorator('hg.admin', 'hg.register.auto_activate',
                               'hg.register.manual_activate')
    def register(self):
        c.auto_active = False
        for perm in User.get_by_username('default').user_perms:
            if perm.permission.permission_name == 'hg.register.auto_activate':
                c.auto_active = True
                break

        if request.POST:

            register_form = RegisterForm()()
            try:
                form_result = register_form.to_python(dict(request.POST))
                form_result['active'] = c.auto_active
                UserModel().create_registration(form_result)
                h.flash(_('You have successfully registered into rhodecode'),
                            category='success')
                Session.commit()
                return redirect(url('login_home'))

            except formencode.Invalid, errors:
                return htmlfill.render(
                    render('/register.html'),
                    defaults=errors.value,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")

        return render('/register.html')

    def password_reset(self):
        if request.POST:
            password_reset_form = PasswordResetForm()()
            try:
                form_result = password_reset_form.to_python(dict(request.POST))
                UserModel().reset_password_link(form_result)
                h.flash(_('Your password reset link was sent'),
                            category='success')
                return redirect(url('login_home'))

            except formencode.Invalid, errors:
                return htmlfill.render(
                    render('/password_reset.html'),
                    defaults=errors.value,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")

        return render('/password_reset.html')

    def password_reset_confirmation(self):
        if request.GET and request.GET.get('key'):
            try:
                user = User.get_by_api_key(request.GET.get('key'))
                data = dict(email=user.email)
                UserModel().reset_password(data)
                h.flash(_('Your password reset was successful, '
                          'new password has been sent to your email'),
                            category='success')
            except Exception, e:
                log.error(e)
                return redirect(url('reset_password'))

        return redirect(url('login_home'))

    def logout(self):
        session.delete()
        log.info('Logging out and deleting session for user')
        redirect(url('home'))
