#!/usr/bin/env python
# encoding: utf-8
# changelog controller for pylons
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
Created on April 21, 2010
changelog controller for pylons
@author: marcink
"""
from pylons import request, session, tmpl_context as c
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel
from webhelpers.paginate import Page
import logging
log = logging.getLogger(__name__)     

class ChangelogController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(ChangelogController, self).__before__()
                
    def index(self):
        limit = 100
        default = 20
        if request.params.get('size'):
            try:
                int_size = int(request.params.get('size'))
            except ValueError:
                int_size = default
            int_size = int_size if int_size <= limit else limit 
            c.size = int_size
            session['changelog_size'] = c.size
            session.save()
        else:
            c.size = session.get('changelog_size', default)

        changesets = HgModel().get_repo(c.repo_name)
            
        p = int(request.params.get('page', 1))
        c.pagination = Page(changesets, page=p, item_count=len(changesets),
                            items_per_page=c.size)
            
        #self._graph(c.repo, c.size,p)
        
        return render('changelog/changelog.html')


    def _graph(self, repo, size, p):
        pass
#        revcount = size
#        if not repo.revisions:return dumps([]), 0
#        
#        max_rev = repo.revisions[-1]
#        offset = 1 if p == 1 else  ((p - 1) * revcount)
#        rev_start = repo.revisions[(-1 * offset)]
#        c.bg_height = 120
#        
#        revcount = min(max_rev, revcount)
#        rev_end = max(0, rev_start - revcount)
#        dag = graph_rev(repo.repo, rev_start, rev_end)
#        
#        c.dag = tree = list(colored(dag))
#        canvasheight = (len(tree) + 1) * c.bg_height - 27
#        data = []
#        for (id, type, ctx, vtx, edges) in tree:
#            if type != CHANGESET:
#                continue
#            node = short(ctx.node())
#            age = _age(ctx.date())
#            desc = ctx.description()
#            user = person(ctx.user())
#            branch = ctx.branch()
#            branch = branch, repo.repo.branchtags().get(branch) == ctx.node()
#            data.append((node, vtx, edges, desc, user, age, branch, ctx.tags()))
#    
#        c.jsdata = dumps(data) 
#        c.canvasheight = canvasheight 

