#!/usr/bin/env python
# encoding: utf-8
# hg controller for pylons
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
Created on February 18, 2010
hg controller for pylons
@author: marcink
"""
from operator import itemgetter
from pylons import tmpl_context as c, request
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel
import logging
log = logging.getLogger(__name__)

class HgController(BaseController):

    @LoginRequired()
    def __before__(self):
        super(HgController, self).__before__()
        
    def index(self):
        c.current_sort = request.GET.get('sort', 'name')
        cs = c.current_sort
        sortables = ['name', 'description', 'last_change', 'tip', 'contact']
        
        if cs not in sortables:
            cs = 'name'
        c.cs_slug = cs.replace('-', '')
        
        cached_repo_list = HgModel().get_repos()
        if cs and c.cs_slug in sortables:
            sort_key = c.cs_slug + '_sort'
            if cs.startswith('-'):
                c.repos_list = sorted(cached_repo_list, key=itemgetter(sort_key), reverse=True)
            else:
                c.repos_list = sorted(cached_repo_list, key=itemgetter(sort_key), reverse=False)
            
        return render('/index.html')
