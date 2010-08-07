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
Created on June 30, 2010
settings controller for pylons
@author: marcink
"""
from formencode import htmlfill
from pylons import tmpl_context as c, request, url
from pylons.controllers.util import redirect
from pylons.i18n.translation import _
from pylons_app.lib.auth import LoginRequired, HasRepoPermissionAllDecorator
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import invalidate_cache
from pylons_app.model.forms import RepoSettingsForm
from pylons_app.model.repo_model import RepoModel
import formencode
import logging
import pylons_app.lib.helpers as h
import traceback

log = logging.getLogger(__name__)

class SettingsController(BaseController):

    @LoginRequired()
    @HasRepoPermissionAllDecorator('repository.admin')           
    def __before__(self):
        super(SettingsController, self).__before__()
        
    def index(self, repo_name):
        repo_model = RepoModel()
        c.repo_info = repo = repo_model.get(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps' 
                      ' it was created or renamed from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')
        
            return redirect(url('repos'))        
        defaults = c.repo_info.__dict__
        defaults.update({'user':c.repo_info.user.username})
        c.users_array = repo_model.get_users_js()
        
        for p in c.repo_info.repo_to_perm:
            defaults.update({'perm_%s' % p.user.username: 
                             p.permission.permission_name})
            
        return htmlfill.render(
            render('settings/repo_settings.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )  

    def update(self, repo_name):
        repo_model = RepoModel()
        changed_name = repo_name
        _form = RepoSettingsForm(edit=True, old_data={'repo_name':repo_name})()
        try:
            form_result = _form.to_python(dict(request.POST))
            repo_model.update(repo_name, form_result)
            invalidate_cache('cached_repo_list')
            h.flash(_('Repository %s updated succesfully' % repo_name),
                    category='success')
            changed_name = form_result['repo_name']               
        except formencode.Invalid as errors:
            c.repo_info = repo_model.get(repo_name)
            c.users_array = repo_model.get_users_js()
            errors.value.update({'user':c.repo_info.user.username})
            return htmlfill.render(
                render('settings/repo_settings.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8") 
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occured during update of repository %s') \
                    % repo_name, category='error')
                    
        return redirect(url('repo_settings_home', repo_name=changed_name))
