#!/usr/bin/env python
# encoding: utf-8
# changeset controller for pylons
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
Created on April 25, 2010
changeset controller for pylons
@author: marcink
"""
from pylons import tmpl_context as c, url, request, response
from pylons.controllers.util import redirect
from pylons_app.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel
from vcs.exceptions import RepositoryError
from vcs.nodes import FileNode
from vcs.utils import diffs as differ
import logging
import traceback

log = logging.getLogger(__name__)

class ChangesetController(BaseController):
    
    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')       
    def __before__(self):
        super(ChangesetController, self).__before__()
        
    def index(self, revision):
        hg_model = HgModel()
        try:
            c.changeset = hg_model.get_repo(c.repo_name).get_changeset(revision)
        except RepositoryError:
            log.error(traceback.format_exc())
            return redirect(url('hg_home'))
        else:
            try:
                c.changeset_old = c.changeset.parents[0]
            except IndexError:
                c.changeset_old = None
            c.changes = []
            
            for node in c.changeset.added:
                filenode_old = FileNode(node.path, '')
                if filenode_old.is_binary or node.is_binary:
                    diff = 'binary file'
                else:    
                    f_udiff = differ.get_udiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_udiff).as_html()

                cs1 = None
                cs2 = node.last_changeset.raw_id                                        
                c.changes.append(('added', node, diff, cs1, cs2))
                
            for node in c.changeset.changed:
                filenode_old = c.changeset_old.get_node(node.path)
                if filenode_old.is_binary or node.is_binary:
                    diff = 'binary file'
                else:    
                    f_udiff = differ.get_udiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_udiff).as_html()

                cs1 = filenode_old.last_changeset.raw_id
                cs2 = node.last_changeset.raw_id                    
                c.changes.append(('changed', node, diff, cs1, cs2))
                
            for node in c.changeset.removed:
                c.changes.append(('removed', node, None, None, None))            
            
        return render('changeset/changeset.html')

    def raw_changeset(self,revision):
        
        hg_model = HgModel()
        try:
            c.changeset = hg_model.get_repo(c.repo_name).get_changeset(revision)
        except RepositoryError:
            log.error(traceback.format_exc())
            return redirect(url('hg_home'))
        else:
            try:
                c.changeset_old = c.changeset.parents[0]
            except IndexError:
                c.changeset_old = None
            c.changes = []
            
            for node in c.changeset.added:
                filenode_old = FileNode(node.path, '')
                if filenode_old.is_binary or node.is_binary:
                    diff = 'binary file'
                else:    
                    f_udiff = differ.get_udiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_udiff).raw_diff()

                cs1 = None
                cs2 = node.last_changeset.raw_id                                        
                c.changes.append(('added', node, diff, cs1, cs2))
                
            for node in c.changeset.changed:
                filenode_old = c.changeset_old.get_node(node.path)
                if filenode_old.is_binary or node.is_binary:
                    diff = 'binary file'
                else:    
                    f_udiff = differ.get_udiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_udiff).raw_diff()

                cs1 = filenode_old.last_changeset.raw_id
                cs2 = node.last_changeset.raw_id                    
                c.changes.append(('changed', node, diff, cs1, cs2))      
        
        response.content_type = 'text/plain'

        parent = True if len(c.changeset.parents) > 0 else False
        c.parent_tmpl = 'Parent  %s' % c.changeset.parents[0]._hex if parent else ''
    
        c.diffs = ''
        for x in c.changes:
            c.diffs += x[2]
            
        return render('changeset/raw_changeset.html')
