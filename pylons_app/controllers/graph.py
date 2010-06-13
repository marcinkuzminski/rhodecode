#!/usr/bin/env python
# encoding: utf-8
# graph controller for pylons
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
graph controller for pylons
@author: marcink
"""
from mercurial.graphmod import revisions as graph_rev, colored, CHANGESET
from mercurial.node import short
from pylons import request, tmpl_context as c
import pylons_app.lib.helpers as h
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel
from simplejson import dumps
from webhelpers.paginate import Page
import logging

log = logging.getLogger(__name__)

class GraphController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(GraphController, self).__before__()
        
    def index(self):
        # Return a rendered template
        hg_model = HgModel()
        if request.POST.get('size'):
            c.size = int(request.params.get('size', 20))
        else:
            c.size = int(request.params.get('size', 20))
        c.jsdata, c.canvasheight = self.graph(hg_model.get_repo(c.repo_name), c.size)
        
        return render('/graph.html')


    def graph(self, repo, size):
        revcount = size
        p = int(request.params.get('page', 1))
        c.pagination = Page(repo.revisions, page=p, item_count=len(repo.revisions), items_per_page=revcount)
        if not repo.revisions:return dumps([]), 0
        
        max_rev = repo.revisions[-1]
        offset = 1 if p == 1 else  ((p - 1) * revcount)
        rev_start = repo.revisions[(-1 * offset)]
        bg_height = 39
        
        revcount = min(max_rev, revcount)
        rev_end = max(0, rev_start - revcount)
        dag = graph_rev(repo.repo, rev_start, rev_end)
        tree = list(colored(dag))
        canvasheight = (len(tree) + 1) * bg_height - 27
        data = []
        for (id, type, ctx, vtx, edges) in tree:
            if type != CHANGESET:
                continue
            node = short(ctx.node())
            age = h.age(ctx.date())
            desc = ctx.description()
            user = h.person(ctx.user())
            branch = ctx.branch()
            branch = branch, repo.repo.branchtags().get(branch) == ctx.node()
            data.append((node, vtx, edges, desc, user, age, branch, ctx.tags()))
    
        return dumps(data), canvasheight
