#!/usr/bin/env python
# encoding: utf-8
# repos controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
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
Created on April 7, 2010
admin controller for pylons
@author: marcink
"""
from operator import itemgetter
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals as g
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _
from pylons_app.lib import helpers as h
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import invalidate_cache
from pylons_app.model.repo_model import RepoModel
from pylons_app.model.hg_model import HgModel
from pylons_app.model.forms import RepoForm
from pylons_app.model.meta import Session
from datetime import datetime
import formencode
from formencode import htmlfill
import logging
import os
import shutil
log = logging.getLogger(__name__)

class ReposController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repo', 'repos')
    @LoginRequired()
    def __before__(self):
        c.admin_user = session.get('admin_user')
        c.admin_username = session.get('admin_username')
        super(ReposController, self).__before__()
                
    def index(self, format='html'):
        """GET /repos: All items in the collection"""
        # url('repos')
        cached_repo_list = HgModel().get_repos()
        c.repos_list = sorted(cached_repo_list, key=itemgetter('name_sort'))
        return render('admin/repos/repos.html')
    
    def create(self):
        """POST /repos: Create a new item"""
        # url('repos')
        repo_model = RepoModel()
        _form = RepoForm()()
        try:
            form_result = _form.to_python(dict(request.POST))
            repo_model.create(form_result, c.hg_app_user)
            invalidate_cache('cached_repo_list')
            h.flash(_('created repository %s') % form_result['repo_name'],
                    category='success')
                                                             
        except formencode.Invalid as errors:
            c.form_errors = errors.error_dict
            c.new_repo = errors.value['repo_name']
            return htmlfill.render(
                 render('admin/repos/repo_add.html'),
                defaults=errors.value,
                encoding="UTF-8")        

        except Exception:
            h.flash(_('error occured during creation of repository %s') \
                    % form_result['repo_name'], category='error')
            
        return redirect('repos')

    def new(self, format='html'):
        """GET /repos/new: Form to create a new item"""
        new_repo = request.GET.get('repo', '')
        c.new_repo = h.repo_name_slug(new_repo)

        return render('admin/repos/repo_add.html')

    def update(self, id):
        """PUT /repos/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repo', id=ID),
        #           method='put')
        # url('repo', id=ID)
        repo_model = RepoModel()
        _form = RepoForm(edit=True)()
        try:
            form_result = _form.to_python(dict(request.POST))
            repo_model.update(id, form_result)
            invalidate_cache('cached_repo_list')
            h.flash(_('Repository updated succesfully'), category='success')
                           
        except formencode.Invalid as errors:
            c.repo_info = repo_model.get(id)
            c.form_errors = errors.error_dict
            return htmlfill.render(
                 render('admin/repos/repo_edit.html'),
                defaults=errors.value,
                encoding="UTF-8")
        except Exception:
            h.flash(_('error occured during update of repository %s') \
                    % form_result['repo_name'], category='error')
        return redirect(url('repos'))
    
    def delete(self, id):
        """DELETE /repos/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repo', id=ID),
        #           method='delete')
        # url('repo', id=ID)
        
        repo_model = RepoModel()
        repo = repo_model.get(id)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps' 
                      ' it was moved or renamed please run the application again'
                      ' in order to rescan repositories') % id, category='error')
        
            return redirect(url('repos'))
        try:
            repo_model.delete(repo)            
            invalidate_cache('cached_repo_list')
            h.flash(_('deleted repository %s') % id, category='success')
        except Exception:
            h.flash(_('An error occured during deletion of %s') % id,
                    category='error')
        
        return redirect(url('repos'))
        
    def show(self, id, format='html'):
        """GET /repos/id: Show a specific item"""
        # url('repo', id=ID)
        
    def edit(self, id, format='html'):
        """GET /repos/id/edit: Form to edit an existing item"""
        # url('edit_repo', id=ID)
        repo_model = RepoModel()
        c.repo_info = repo_model.get(id)
        defaults = c.repo_info.__dict__
        defaults.update({'user':c.repo_info.user.username})        
        return htmlfill.render(
            render('admin/repos/repo_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )          
