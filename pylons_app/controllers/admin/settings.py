#!/usr/bin/env python
# encoding: utf-8
# settings controller for pylons
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
Created on July 14, 2010
settings controller for pylons
@author: marcink
"""
from formencode import htmlfill
from pylons import request, session, tmpl_context as c, url, app_globals as g, \
    config
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from pylons_app.lib import helpers as h
from pylons_app.lib.auth import LoginRequired, HasPermissionAllDecorator, \
    HasPermissionAnyDecorator
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import repo2db_mapper, invalidate_cache, \
    set_hg_app_config, get_hg_settings, get_hg_ui_settings, make_ui
from pylons_app.model.db import User, UserLog, HgAppSettings, HgAppUi
from pylons_app.model.forms import UserForm, ApplicationSettingsForm, \
    ApplicationUiSettingsForm
from pylons_app.model.hg_model import HgModel
from pylons_app.model.user_model import UserModel
import formencode
import logging
import traceback
 
log = logging.getLogger(__name__)


class SettingsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('setting', 'settings', controller='admin/settings', 
    #         path_prefix='/admin', name_prefix='admin_')


    @LoginRequired()
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(SettingsController, self).__before__()
    
    
    @HasPermissionAllDecorator('hg.admin')    
    def index(self, format='html'):
        """GET /admin/settings: All items in the collection"""
        # url('admin_settings')

        defaults = get_hg_settings()
        defaults.update(get_hg_ui_settings())
        return htmlfill.render(
            render('admin/settings/settings.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )  
    
    @HasPermissionAllDecorator('hg.admin')
    def create(self):
        """POST /admin/settings: Create a new item"""
        # url('admin_settings')
    
    @HasPermissionAllDecorator('hg.admin')
    def new(self, format='html'):
        """GET /admin/settings/new: Form to create a new item"""
        # url('admin_new_setting')
        
    @HasPermissionAllDecorator('hg.admin')
    def update(self, setting_id):
        """PUT /admin/settings/setting_id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('admin_setting', setting_id=ID),
        #           method='put')
        # url('admin_setting', setting_id=ID)
        if setting_id == 'mapping':
            rm_obsolete = request.POST.get('destroy', False)
            log.debug('Rescanning directories with destroy=%s', rm_obsolete)

            initial = HgModel.repo_scan(g.paths[0][0], g.paths[0][1], g.baseui)
            repo2db_mapper(initial, rm_obsolete)
            invalidate_cache('cached_repo_list')
            h.flash(_('Repositories sucessfully rescanned'), category='success')            
        
        if setting_id == 'global':
            
            application_form = ApplicationSettingsForm()()
            try:
                form_result = application_form.to_python(dict(request.POST))
            
                try:
                    hgsettings1 = self.sa.query(HgAppSettings)\
                    .filter(HgAppSettings.app_settings_name == 'title').one()
                    hgsettings1.app_settings_value = form_result['hg_app_title'] 
                    
                    hgsettings2 = self.sa.query(HgAppSettings)\
                    .filter(HgAppSettings.app_settings_name == 'realm').one()
                    hgsettings2.app_settings_value = form_result['hg_app_realm'] 
                    
                    
                    self.sa.add(hgsettings1)
                    self.sa.add(hgsettings2)
                    self.sa.commit()
                    set_hg_app_config(config)
                    h.flash(_('Updated application settings'),
                            category='success')
                                    
                except:
                    log.error(traceback.format_exc())
                    h.flash(_('error occured during updating application settings'),
                            category='error')
                                
                    self.sa.rollback()
                    

            except formencode.Invalid as errors:
                return htmlfill.render(
                     render('admin/settings/settings.html'),
                     defaults=errors.value,
                     errors=errors.error_dict or {},
                     prefix_error=False,
                     encoding="UTF-8") 
        
        if setting_id == 'mercurial':
            application_form = ApplicationUiSettingsForm()()
            try:
                form_result = application_form.to_python(dict(request.POST))
            
                try:
                    
                    hgsettings1 = self.sa.query(HgAppUi)\
                    .filter(HgAppUi.ui_key == 'push_ssl').one()
                    hgsettings1.ui_value = form_result['web_push_ssl']
                    
                    hgsettings2 = self.sa.query(HgAppUi)\
                    .filter(HgAppUi.ui_key == '/').one()
                    hgsettings2.ui_value = form_result['paths_root_path']                    
                    
                    self.sa.add(hgsettings1)
                    self.sa.add(hgsettings2)
                    self.sa.commit()
                    
                    h.flash(_('Updated application settings'),
                            category='success')
                                    
                except:
                    log.error(traceback.format_exc())
                    h.flash(_('error occured during updating application settings'),
                            category='error')
                                
                    self.sa.rollback()
                    

            except formencode.Invalid as errors:
                return htmlfill.render(
                     render('admin/settings/settings.html'),
                     defaults=errors.value,
                     errors=errors.error_dict or {},
                     prefix_error=False,
                     encoding="UTF-8") 
                
                
                        
        return redirect(url('admin_settings'))
    
    @HasPermissionAllDecorator('hg.admin')
    def delete(self, setting_id):
        """DELETE /admin/settings/setting_id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('admin_setting', setting_id=ID),
        #           method='delete')
        # url('admin_setting', setting_id=ID)
    
    @HasPermissionAllDecorator('hg.admin')
    def show(self, setting_id, format='html'):
        """GET /admin/settings/setting_id: Show a specific item"""
        # url('admin_setting', setting_id=ID)
    
    @HasPermissionAllDecorator('hg.admin')         
    def edit(self, setting_id, format='html'):
        """GET /admin/settings/setting_id/edit: Form to edit an existing item"""
        # url('admin_edit_setting', setting_id=ID)


    def my_account(self):
        """
        GET /_admin/my_account Displays info about my account 
        """
        # url('admin_settings_my_account')
        c.user = self.sa.query(User).get(c.hg_app_user.user_id)
        if c.user.username == 'default':
            h.flash(_("You can't edit this user since it's" 
              " crucial for entire application"), category='warning')
            return redirect(url('users'))
        
        defaults = c.user.__dict__
        return htmlfill.render(
            render('admin/users/user_edit_my_account.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        ) 

    def my_account_update(self):
        """PUT /_admin/my_account_update: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('admin_settings_my_account_update'),
        #           method='put')
        # url('admin_settings_my_account_update', id=ID)
        user_model = UserModel()
        uid = c.hg_app_user.user_id
        _form = UserForm(edit=True, old_data={'user_id':uid})()
        form_result = {}
        try:
            form_result = _form.to_python(dict(request.POST))
            user_model.update_my_account(uid, form_result)
            h.flash(_('Your account was updated succesfully'), category='success')
                           
        except formencode.Invalid as errors:
            #c.user = self.sa.query(User).get(c.hg_app_user.user_id)
            return htmlfill.render(
                render('admin/users/user_edit_my_account.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occured during update of user %s') \
                    % form_result.get('username'), category='error')
                    
        return redirect(url('my_account'))
    
    @HasPermissionAnyDecorator('repository.create', 'hg.admin')
    def create_repository(self):
        """GET /_admin/create_repository: Form to create a new item"""
        new_repo = request.GET.get('repo', '')
        c.new_repo = h.repo_name_slug(new_repo)

        return render('admin/repos/repo_add_create_repository.html')
        
