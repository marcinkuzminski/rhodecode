# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.files
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Files controller for RhodeCode
    
    :created_on: Apr 21, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
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
import tempfile
import logging
import rhodecode.lib.helpers as h

from mercurial import archival

from pylons import request, response, session, tmpl_context as c, url
from pylons.i18n.translation import _
from pylons.controllers.util import redirect

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import EmptyChangeset
from rhodecode.model.scm import ScmModel

from vcs.exceptions import RepositoryError, ChangesetError, \
    ChangesetDoesNotExistError, EmptyRepositoryError
from vcs.nodes import FileNode
from vcs.utils import diffs as differ

log = logging.getLogger(__name__)

class FilesController(BaseController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(FilesController, self).__before__()
        c.cut_off_limit = self.cut_off_limit

    def index(self, repo_name, revision, f_path):
        hg_model = ScmModel()
        c.repo = hg_model.get_repo(c.repo_name)

        try:
            #reditect to given revision from form
            post_revision = request.POST.get('at_rev', None)
            if post_revision:
                post_revision = c.repo.get_changeset(post_revision).raw_id
                redirect(url('files_home', repo_name=c.repo_name,
                             revision=post_revision, f_path=f_path))

            c.branch = request.GET.get('branch', None)

            c.f_path = f_path

            c.changeset = c.repo.get_changeset(revision)
            cur_rev = c.changeset.revision

            #prev link
            try:
                prev_rev = c.repo.get_changeset(cur_rev).prev(c.branch).raw_id
                c.url_prev = url('files_home', repo_name=c.repo_name,
                             revision=prev_rev, f_path=f_path)
                if c.branch:
                    c.url_prev += '?branch=%s' % c.branch
            except ChangesetDoesNotExistError:
                c.url_prev = '#'

            #next link
            try:
                next_rev = c.repo.get_changeset(cur_rev).next(c.branch).raw_id
                c.url_next = url('files_home', repo_name=c.repo_name,
                         revision=next_rev, f_path=f_path)
                if c.branch:
                    c.url_next += '?branch=%s' % c.branch
            except ChangesetDoesNotExistError:
                c.url_next = '#'

            #files
            try:
                c.files_list = c.changeset.get_node(f_path)
                c.file_history = self._get_history(c.repo, c.files_list, f_path)
            except RepositoryError, e:
                h.flash(str(e), category='warning')
                redirect(h.url('files_home', repo_name=repo_name, revision=revision))

        except EmptyRepositoryError, e:
            h.flash(_('There are no files yet'), category='warning')
            redirect(h.url('summary_home', repo_name=repo_name))

        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('files_home', repo_name=repo_name, revision='tip'))



        return render('files/files.html')

    def rawfile(self, repo_name, revision, f_path):
        hg_model = ScmModel()
        c.repo = hg_model.get_repo(c.repo_name)
        file_node = c.repo.get_changeset(revision).get_node(f_path)
        response.content_type = file_node.mimetype
        response.content_disposition = 'attachment; filename=%s' \
                                                    % f_path.split('/')[-1]
        return file_node.content

    def raw(self, repo_name, revision, f_path):
        hg_model = ScmModel()
        c.repo = hg_model.get_repo(c.repo_name)
        file_node = c.repo.get_changeset(revision).get_node(f_path)
        response.content_type = 'text/plain'

        return file_node.content

    def annotate(self, repo_name, revision, f_path):
        hg_model = ScmModel()
        c.repo = hg_model.get_repo(c.repo_name)

        try:
            c.cs = c.repo.get_changeset(revision)
            c.file = c.cs.get_node(f_path)
        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('files_home', repo_name=repo_name, revision=revision))

        c.file_history = self._get_history(c.repo, c.file, f_path)

        c.f_path = f_path

        return render('files/files_annotate.html')

    def archivefile(self, repo_name, fname):
        archive_specs = {
          '.tar.bz2': ('application/x-tar', 'tbz2'),
          '.tar.gz': ('application/x-tar', 'tgz'),
          '.zip': ('application/zip', 'zip'),
        }

        fileformat = None
        revision = None

        for ext in archive_specs.keys():
            archive_spec = fname.split(ext)
            if len(archive_spec) == 2:
                fileformat = archive_spec[1] or ext
                revision = archive_spec[0]

        if not archive_specs.has_key(fileformat):
            return _('Unknown archive type')

        repo = ScmModel().get_repo(repo_name)

        try:
            repo.get_changeset(revision)
        except ChangesetDoesNotExistError:
            return _('Unknown revision %s') % revision
        except EmptyRepositoryError:
            return _('Empty repository')

        archive = tempfile.TemporaryFile()
        localrepo = repo.repo
        fname = '%s-%s%s' % (repo_name, revision, fileformat)
        archival.archive(localrepo, archive, revision, archive_specs[fileformat][1],
                         prefix='%s-%s' % (repo_name, revision))
        response.content_type = archive_specs[fileformat][0]
        response.content_disposition = 'attachment; filename=%s' % fname
        archive.seek(0)

        def read_in_chunks(file_object, chunk_size=1024 * 40):
            """Lazy function (generator) to read a file piece by piece.
            Default chunk size: 40k."""
            while True:
                data = file_object.read(chunk_size)
                if not data:
                    break
                yield data

        return read_in_chunks(archive)

    def diff(self, repo_name, f_path):
        hg_model = ScmModel()
        diff1 = request.GET.get('diff1')
        diff2 = request.GET.get('diff2')
        c.action = request.GET.get('diff')
        c.no_changes = diff1 == diff2
        c.f_path = f_path
        c.repo = hg_model.get_repo(c.repo_name)

        try:
            if diff1 not in ['', None, 'None', '0' * 12, '0' * 40]:
                c.changeset_1 = c.repo.get_changeset(diff1)
                node1 = c.changeset_1.get_node(f_path)
            else:
                c.changeset_1 = EmptyChangeset()
                node1 = FileNode('.', '', changeset=c.changeset_1)

            if diff2 not in ['', None, 'None', '0' * 12, '0' * 40]:
                c.changeset_2 = c.repo.get_changeset(diff2)
                node2 = c.changeset_2.get_node(f_path)
            else:
                c.changeset_2 = EmptyChangeset()
                node2 = FileNode('.', '', changeset=c.changeset_2)
        except RepositoryError:
            return redirect(url('files_home',
                                repo_name=c.repo_name, f_path=f_path))

        f_udiff = differ.get_udiff(node1, node2)
        diff = differ.DiffProcessor(f_udiff)

        if c.action == 'download':
            diff_name = '%s_vs_%s.diff' % (diff1, diff2)
            response.content_type = 'text/plain'
            response.content_disposition = 'attachment; filename=%s' \
                                                    % diff_name
            return diff.raw_diff()

        elif c.action == 'raw':
            response.content_type = 'text/plain'
            return diff.raw_diff()

        elif c.action == 'diff':
            if node1.size > self.cut_off_limit or node2.size > self.cut_off_limit:
                c.cur_diff = _('Diff is to big to display')
            else:
                c.cur_diff = diff.as_html()
        else:
            #default option
            if node1.size > self.cut_off_limit or node2.size > self.cut_off_limit:
                c.cur_diff = _('Diff is to big to display')
            else:
                c.cur_diff = diff.as_html()

        if not c.cur_diff: c.no_changes = True
        return render('files/file_diff.html')

    def _get_history(self, repo, node, f_path):
        from vcs.nodes import NodeKind
        if not node.kind is NodeKind.FILE:
            return []
        changesets = node.history
        hist_l = []

        changesets_group = ([], _("Changesets"))
        branches_group = ([], _("Branches"))
        tags_group = ([], _("Tags"))

        for chs in changesets:
            n_desc = 'r%s:%s' % (chs.revision, chs.short_id)
            changesets_group[0].append((chs.raw_id, n_desc,))

        hist_l.append(changesets_group)

        for name, chs in c.repository_branches.items():
            #chs = chs.split(':')[-1]
            branches_group[0].append((chs, name),)
        hist_l.append(branches_group)

        for name, chs in c.repository_tags.items():
            #chs = chs.split(':')[-1]
            tags_group[0].append((chs, name),)
        hist_l.append(tags_group)

        return hist_l

