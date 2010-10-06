#!/usr/bin/env python
# encoding: utf-8
# login controller for pylons
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

"""
Created on April 22, 2010
login controller for pylons
@author: marcink
"""
from formencode import htmlfill
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from rhodecode.lib.auth import AuthUser, HasPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
import rhodecode.lib.helpers as h 
from pylons.i18n.translation import _
from rhodecode.model.forms import LoginForm, RegisterForm, PasswordResetForm
from rhodecode.model.user_model import UserModel
import formencode
import logging

log = logging.getLogger(__name__)

class LoginController(BaseController):

    def __before__(self):
        super(LoginController, self).__before__()

    def index(self):
        #redirect if already logged in
        c.came_from = request.GET.get('came_from', None)
        
        if c.rhodecode_user.is_authenticated:
            return redirect(url('hg_home'))
        
        if request.POST:
            #import Login Form validator class
            login_form = LoginForm()
            try:
                c.form_result = login_form.to_python(dict(request.POST))
                username = c.form_result['username']
                user = UserModel().get_user_by_name(username)
                auth_user = AuthUser()
                auth_user.username = user.username
                auth_user.is_authenticated = True
                auth_user.is_admin = user.admin
                auth_user.user_id = user.user_id
                auth_user.name = user.name
                auth_user.lastname = user.lastname
                session['rhodecode_user'] = auth_user
                session.save()
                log.info('user %s is now authenticated', username)
                
                user.update_lastlogin()
                                        
                if c.came_from:
                    return redirect(c.came_from)
                else:
                    return redirect(url('hg_home'))
                               
            except formencode.Invalid as errors:
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
        user_model = UserModel()
        c.auto_active = False
        for perm in user_model.get_default().user_perms:
            if perm.permission.permission_name == 'hg.register.auto_activate':
                c.auto_active = True
                break
                        
        if request.POST:
                
            register_form = RegisterForm()()
            try:
                form_result = register_form.to_python(dict(request.POST))
                form_result['active'] = c.auto_active
                user_model.create_registration(form_result)
                h.flash(_('You have successfully registered into hg-app'),
                            category='success')                
                return redirect(url('login_home'))
                               
            except formencode.Invalid as errors:
                return htmlfill.render(
                    render('/register.html'),
                    defaults=errors.value,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")
        
        return render('/register.html')

    def password_reset(self):
        user_model = UserModel()
        if request.POST:
                
            password_reset_form = PasswordResetForm()()
            try:
                form_result = password_reset_form.to_python(dict(request.POST))
                user_model.reset_password(form_result)
                h.flash(_('Your new password was sent'),
                            category='success')                 
                return redirect(url('login_home'))
                               
            except formencode.Invalid as errors:
                return htmlfill.render(
                    render('/password_reset.html'),
                    defaults=errors.value,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")
        
        return render('/password_reset.html')
        
    def logout(self):
        session['rhodecode_user'] = AuthUser()
        session.save()
        log.info('Logging out and setting user as Empty')
        redirect(url('hg_home'))
