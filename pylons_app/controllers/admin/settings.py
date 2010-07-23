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
from pylons_app.lib.auth import LoginRequired, HasPermissionAllDecorator
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import repo2db_mapper, invalidate_cache, \
    set_hg_app_config
from pylons_app.model.db import User, UserLog, HgAppSettings
from pylons_app.model.forms import UserForm, ApplicationSettingsForm
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
    #@HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(SettingsController, self).__before__()
        
    def index(self, format='html'):
        """GET /admin/settings: All items in the collection"""
        # url('admin_settings')

        hgsettings = self.sa.query(HgAppSettings).scalar()
        defaults = hgsettings.__dict__ if hgsettings else {}
        return htmlfill.render(
            render('admin/settings/settings.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )  
    
    def create(self):
        """POST /admin/settings: Create a new item"""
        # url('admin_settings')

    def new(self, format='html'):
        """GET /admin/settings/new: Form to create a new item"""
        # url('admin_new_setting')

    def update(self, id):
        """PUT /admin/settings/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('admin_setting', id=ID),
        #           method='put')
        # url('admin_setting', id=ID)
        if id == 'mapping':
            rm_obsolete = request.POST.get('destroy', False)
            log.debug('Rescanning directories with destroy=%s', rm_obsolete)

            initial = HgModel.repo_scan(g.paths[0][0], g.paths[0][1], g.baseui)
            repo2db_mapper(initial, rm_obsolete)
            invalidate_cache('cached_repo_list')
            h.flash(_('Repositories sucessfully rescanned'), category='success')            
        
        if id == 'global':
            
            application_form = ApplicationSettingsForm()()
            try:
                form_result = application_form.to_python(dict(request.POST))
                title = form_result['app_title']
                realm = form_result['app_auth_realm']
            
                try:
                    hgsettings = self.sa.query(HgAppSettings).get(1)
                    hgsettings.app_auth_realm = realm
                    hgsettings.app_title = title
                    
                    self.sa.add(hgsettings)
                    self.sa.commit()
                    set_hg_app_config(config)
                    h.flash(_('Updated application settings'),
                            category='success')
                                    
                except:
                    log.error(traceback.format_exc())
                    h.flash(_('error occured during chaning application settings'),
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

    def delete(self, id):
        """DELETE /admin/settings/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('admin_setting', id=ID),
        #           method='delete')
        # url('admin_setting', id=ID)

    def show(self, id, format='html'):
        """GET /admin/settings/id: Show a specific item"""
        # url('admin_setting', id=ID)

    def edit(self, id, format='html'):
        """GET /admin/settings/id/edit: Form to edit an existing item"""
        # url('admin_edit_setting', id=ID)
