#!/usr/bin/env python
# encoding: utf-8
# files controller for pylons
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
files controller for pylons
@author: marcink
"""
from mercurial import archival
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import redirect
from pylons_app.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import EmptyChangeset
from pylons_app.model.hg_model import HgModel
from vcs.exceptions import RepositoryError, ChangesetError
from vcs.nodes import FileNode
from vcs.utils import diffs as differ
import logging
import pylons_app.lib.helpers as h
import tempfile
        
log = logging.getLogger(__name__)

class FilesController(BaseController):
    
    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')       
    def __before__(self):
        super(FilesController, self).__before__()

    def index(self, repo_name, revision, f_path):
        hg_model = HgModel()
        c.repo = repo = hg_model.get_repo(c.repo_name)
        revision = request.POST.get('at_rev', None) or revision
        
        def get_next_rev(cur):
            max_rev = len(c.repo.revisions) - 1
            r = cur + 1
            if r > max_rev:
                r = max_rev
            return r
            
        def get_prev_rev(cur):
            r = cur - 1
            return r

        c.f_path = f_path
     
        
        try:
            cur_rev = repo.get_changeset(revision).revision
            prev_rev = repo.get_changeset(get_prev_rev(cur_rev)).raw_id
            next_rev = repo.get_changeset(get_next_rev(cur_rev)).raw_id
                    
            c.url_prev = url('files_home', repo_name=c.repo_name,
                             revision=prev_rev, f_path=f_path) 
            c.url_next = url('files_home', repo_name=c.repo_name,
                             revision=next_rev, f_path=f_path)   
                    
            c.changeset = repo.get_changeset(revision)

                        
            c.cur_rev = c.changeset.raw_id
            c.rev_nr = c.changeset.revision
            c.files_list = c.changeset.get_node(f_path)
            c.file_history = self._get_history(repo, c.files_list, f_path)
            
        except (RepositoryError, ChangesetError):
            c.files_list = None
        
        return render('files/files.html')

    def rawfile(self, repo_name, revision, f_path):
        hg_model = HgModel()
        c.repo = hg_model.get_repo(c.repo_name)
        file_node = c.repo.get_changeset(revision).get_node(f_path)
        response.content_type = file_node.mimetype
        response.content_disposition = 'attachment; filename=%s' \
                                                    % f_path.split('/')[-1] 
        return file_node.content
    
    def annotate(self, repo_name, revision, f_path):
        hg_model = HgModel()
        c.repo = hg_model.get_repo(c.repo_name)
        cs = c.repo.get_changeset(revision)
        c.file = cs.get_node(f_path)
        c.file_msg = cs.get_file_message(f_path)
        c.cur_rev = cs.raw_id
        c.rev_nr = cs.revision        
        c.f_path = f_path

        return render('files/files_annotate.html')
      
    def archivefile(self, repo_name, revision, fileformat):
        archive_specs = {
          '.tar.bz2': ('application/x-tar', 'tbz2'),
          '.tar.gz': ('application/x-tar', 'tgz'),
          '.zip': ('application/zip', 'zip'),
        }
        if not archive_specs.has_key(fileformat):
            return 'Unknown archive type %s' % fileformat
                        
        def read_in_chunks(file_object, chunk_size=1024 * 40):
            """Lazy function (generator) to read a file piece by piece.
            Default chunk size: 40k."""
            while True:
                data = file_object.read(chunk_size)
                if not data:
                    break
                yield data        
            
        archive = tempfile.TemporaryFile()
        repo = HgModel().get_repo(repo_name).repo
        fname = '%s-%s%s' % (repo_name, revision, fileformat)
        archival.archive(repo, archive, revision, archive_specs[fileformat][1],
                         prefix='%s-%s' % (repo_name, revision))
        response.content_type = archive_specs[fileformat][0]
        response.content_disposition = 'attachment; filename=%s' % fname
        archive.seek(0)
        return read_in_chunks(archive)
    
    def diff(self, repo_name, f_path):
        hg_model = HgModel()
        diff1 = request.GET.get('diff1')
        diff2 = request.GET.get('diff2')
        c.action = request.GET.get('diff')
        c.no_changes = diff1 == diff2
        c.f_path = f_path
        c.repo = hg_model.get_repo(c.repo_name)

        try:
            if diff1 not in ['', None, 'None', '0' * 12]:
                c.changeset_1 = c.repo.get_changeset(diff1)
                node1 = c.changeset_1.get_node(f_path)
            else:
                c.changeset_1 = EmptyChangeset()
                node1 = FileNode('.', '')
            if diff2 not in ['', None, 'None', '0' * 12]:
                c.changeset_2 = c.repo.get_changeset(diff2)
                node2 = c.changeset_2.get_node(f_path)
            else:
                c.changeset_2 = EmptyChangeset()
                node2 = FileNode('.', '') 
        except RepositoryError:
            return redirect(url('files_home',
                                repo_name=c.repo_name, f_path=f_path))

        c.diff1 = 'r%s:%s' % (c.changeset_1.revision, c.changeset_1.raw_id)
        c.diff2 = 'r%s:%s' % (c.changeset_2.revision, c.changeset_2.raw_id)
        f_udiff = differ.get_udiff(node1, node2)
        
        diff = differ.DiffProcessor(f_udiff)
                                
        if c.action == 'download':
            diff_name = '%s_vs_%s.diff' % (diff1, diff2)
            response.content_type = 'text/plain'
            response.content_disposition = 'attachment; filename=%s' \
                                                    % diff_name             
            return diff.raw_diff()
        
        elif c.action == 'raw':
            c.cur_diff = '<pre class="raw">%s</pre>' % h.escape(diff.raw_diff())
        elif c.action == 'diff':
            c.cur_diff = diff.as_html()
        else:
            #default option
            c.cur_diff = diff.as_html()
        
        if not c.cur_diff: c.no_changes = True    
        return render('files/file_diff.html')
    
    def _get_history(self, repo, node, f_path):
        from vcs.nodes import NodeKind
        if not node.kind is NodeKind.FILE:
            return []
        changesets = node.history
        hist_l = []
        for chs in changesets:
            n_desc = 'r%s:%s' % (chs.revision, chs._short)
            hist_l.append((chs._short, n_desc,))
        return hist_l
