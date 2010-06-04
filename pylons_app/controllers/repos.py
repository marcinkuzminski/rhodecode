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
import logging
from pylons import request, response, session, tmpl_context as c, url, \
    app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib.auth import LoginRequired
from pylons.i18n.translation import _
from pylons_app.lib import helpers as h
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.filters import clean_repo
from pylons_app.lib.utils import check_repo, invalidate_cache
from pylons_app.model.hg_model import HgModel
import os
import shutil
from operator import itemgetter
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
        name = request.POST.get('name')

        try:
            self._create_repo(name)
            #clear our cached list for refresh with new repo
            invalidate_cache('cached_repo_list')
            h.flash(_('created repository %s') % name, category='success')
        except Exception as e:
            log.error(e)
        
        return redirect('repos')
        
    def _create_repo(self, repo_name):        
        repo_path = os.path.join(g.base_path, repo_name)
        if check_repo(repo_name, g.base_path):
            log.info('creating repo %s in %s', repo_name, repo_path)
            from vcs.backends.hg import MercurialRepository
            MercurialRepository(repo_path, create=True)
                        

    def new(self, format='html'):
        """GET /repos/new: Form to create a new item"""
        new_repo = request.GET.get('repo', '')
        c.new_repo = clean_repo(new_repo)

        return render('admin/repos/repo_add.html')

    def update(self, id):
        """PUT /repos/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repo', id=ID),
        #           method='put')
        # url('repo', id=ID)

    def delete(self, id):
        """DELETE /repos/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repo', id=ID),
        #           method='delete')
        # url('repo', id=ID)
        from datetime import datetime
        path = g.paths[0][1].replace('*', '')
        rm_path = os.path.join(path, id)
        log.info("Removing %s", rm_path)
        shutil.move(os.path.join(rm_path, '.hg'), os.path.join(rm_path, 'rm__.hg'))
        shutil.move(rm_path, os.path.join(path, 'rm__%s-%s' % (datetime.today(), id)))
        
        #clear our cached list for refresh with new repo
        invalidate_cache('cached_repo_list')
        h.flash(_('deleted repository %s') % rm_path, category='success')            
        return redirect(url('repos'))
        

    def show(self, id, format='html'):
        """GET /repos/id: Show a specific item"""
        # url('repo', id=ID)
        
    def edit(self, id, format='html'):
        """GET /repos/id/edit: Form to edit an existing item"""
        # url('edit_repo', id=ID)
        c.new_repo = id
        return render('admin/repos/repo_edit.html')
