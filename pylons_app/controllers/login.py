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
from pylons_app.lib.auth import AuthUser, HasPermissionAnyDecorator
from pylons_app.lib.base import BaseController, render
from pylons_app.model.forms import LoginForm, RegisterForm
from pylons_app.model.user_model import UserModel
import formencode
import logging

log = logging.getLogger(__name__)

class LoginController(BaseController):

    def __before__(self):
        super(LoginController, self).__before__()

    def index(self):
        #redirect if already logged in
        if c.hg_app_user.is_authenticated:
            return redirect(url('hg_home'))
        
        if request.POST:
            #import Login Form validator class
            login_form = LoginForm()
            try:
                c.form_result = login_form.to_python(dict(request.POST))
                return redirect(url('hg_home'))
                               
            except formencode.Invalid as errors:
                return htmlfill.render(
                    render('/login.html'),
                    defaults=errors.value,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")
                        
        return render('/login.html')
    
    @HasPermissionAnyDecorator('hg.admin', 'hg.register.auto_activate', 'hg.register.manual_activate')
    def register(self):
        user_model = UserModel()
        c.auto_active = False
        for perm in user_model.get_default().user_perms:
            print perm.permission.permission_name
            if perm.permission.permission_name == 'hg.register.auto_activate':
                c.auto_active = True
                break
                        
        if request.POST:
                
            register_form = RegisterForm()()
            try:
                form_result = register_form.to_python(dict(request.POST))
                form_result['active'] = c.auto_active
                user_model.create_registration(form_result)
                return redirect(url('login_home'))
                               
            except formencode.Invalid as errors:
                return htmlfill.render(
                    render('/register.html'),
                    defaults=errors.value,
                    errors=errors.error_dict or {},
                    prefix_error=False,
                    encoding="UTF-8")
        
        return render('/register.html')
    
    def logout(self):
        session['hg_app_user'] = AuthUser()
        session.save()
        log.info('Logging out and setting user as Empty')
        redirect(url('hg_home'))
