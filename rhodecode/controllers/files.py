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

import logging
import tempfile
import rhodecode.lib.helpers as h

from pylons import request, response, session, tmpl_context as c, url
from pylons.i18n.translation import _
from pylons.controllers.util import redirect

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.utils import EmptyChangeset
from rhodecode.model.repo import RepoModel

from vcs.backends import ARCHIVE_SPECS
from vcs.exceptions import RepositoryError, ChangesetDoesNotExistError, \
    EmptyRepositoryError, ImproperArchiveTypeError, VCSError
from vcs.nodes import FileNode, NodeKind
from vcs.utils import diffs as differ

log = logging.getLogger(__name__)


class FilesController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(FilesController, self).__before__()
        c.cut_off_limit = self.cut_off_limit

    def __get_cs_or_redirect(self, rev, repo_name):
        """
        Safe way to get changeset if error occur it redirects to tip with
        proper message
        
        :param rev: revision to fetch
        :param repo_name: repo name to redirect after
        """

        try:
            return c.rhodecode_repo.get_changeset(rev)
        except EmptyRepositoryError, e:
            h.flash(_('There are no files yet'), category='warning')
            redirect(h.url('summary_home', repo_name=repo_name))

        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('files_home', repo_name=repo_name, revision='tip'))

    def index(self, repo_name, revision, f_path):
        #reditect to given revision from form if given
        post_revision = request.POST.get('at_rev', None)
        if post_revision:
            cs = self.__get_cs_or_redirect(revision, repo_name)
            redirect(url('files_home', repo_name=c.repo_name,
                         revision=cs.raw_id, f_path=f_path))


        c.changeset = self.__get_cs_or_redirect(revision, repo_name)
        c.branch = request.GET.get('branch', None)
        c.f_path = f_path

        cur_rev = c.changeset.revision

        #prev link
        try:
            prev_rev = c.rhodecode_repo.get_changeset(cur_rev).prev(c.branch)
            c.url_prev = url('files_home', repo_name=c.repo_name,
                         revision=prev_rev.raw_id, f_path=f_path)
            if c.branch:
                c.url_prev += '?branch=%s' % c.branch
        except (ChangesetDoesNotExistError, VCSError):
            c.url_prev = '#'

        #next link
        try:
            next_rev = c.rhodecode_repo.get_changeset(cur_rev).next(c.branch)
            c.url_next = url('files_home', repo_name=c.repo_name,
                     revision=next_rev.raw_id, f_path=f_path)
            if c.branch:
                c.url_next += '?branch=%s' % c.branch
        except (ChangesetDoesNotExistError, VCSError):
            c.url_next = '#'

        #files
        try:
            c.files_list = c.changeset.get_node(f_path)
            c.file_history = self._get_history(c.rhodecode_repo,
                                               c.files_list, f_path)
        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('files_home', repo_name=repo_name,
                           revision=revision))


        return render('files/files.html')

    def rawfile(self, repo_name, revision, f_path):
        cs = self.__get_cs_or_redirect(revision, repo_name)
        try:
            file_node = cs.get_node(f_path)
        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('files_home', repo_name=repo_name,
                           revision=cs.raw_id))

        fname = f_path.split('/')[-1].encode('utf8', 'replace')
        response.content_type = file_node.mimetype
        response.content_disposition = 'attachment; filename=%s' % fname
        return file_node.content

    def raw(self, repo_name, revision, f_path):
        cs = self.__get_cs_or_redirect(revision, repo_name)
        try:
            file_node = cs.get_node(f_path)
        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('files_home', repo_name=repo_name,
                           revision=cs.raw_id))

        response.content_type = 'text/plain'

        return file_node.content

    def annotate(self, repo_name, revision, f_path):
        cs = self.__get_cs_or_redirect(revision, repo_name)
        try:
            c.file = cs.get_node(f_path)
        except RepositoryError, e:
            h.flash(str(e), category='warning')
            redirect(h.url('files_home', repo_name=repo_name,
                           revision=cs.raw_id))

        c.file_history = self._get_history(c.rhodecode_repo,
                                           c.file, f_path)
        c.cs = cs
        c.f_path = f_path

        return render('files/files_annotate.html')

    def archivefile(self, repo_name, fname):

        fileformat = None
        revision = None
        ext = None

        for a_type, ext_data in ARCHIVE_SPECS.items():
            archive_spec = fname.split(ext_data[1])
            if len(archive_spec) == 2 and archive_spec[1] == '':
                fileformat = a_type or ext_data[1]
                revision = archive_spec[0]
                ext = ext_data[1]

        try:
            dbrepo = RepoModel().get_by_repo_name(repo_name)
            if dbrepo.enable_downloads is False:
                return _('downloads disabled')

            cs = c.rhodecode_repo.get_changeset(revision)
            content_type = ARCHIVE_SPECS[fileformat][0]
        except ChangesetDoesNotExistError:
            return _('Unknown revision %s') % revision
        except EmptyRepositoryError:
            return _('Empty repository')
        except (ImproperArchiveTypeError, KeyError):
            return _('Unknown archive type')

        response.content_type = content_type
        response.content_disposition = 'attachment; filename=%s-%s%s' \
            % (repo_name, revision, ext)

        return cs.get_chunked_archive(stream=tempfile.TemporaryFile(),
                                      kind=fileformat)


    def diff(self, repo_name, f_path):
        diff1 = request.GET.get('diff1')
        diff2 = request.GET.get('diff2')
        c.action = request.GET.get('diff')
        c.no_changes = diff1 == diff2
        c.f_path = f_path

        try:
            if diff1 not in ['', None, 'None', '0' * 12, '0' * 40]:
                c.changeset_1 = c.rhodecode_repo.get_changeset(diff1)
                node1 = c.changeset_1.get_node(f_path)
            else:
                c.changeset_1 = EmptyChangeset()
                node1 = FileNode('.', '', changeset=c.changeset_1)

            if diff2 not in ['', None, 'None', '0' * 12, '0' * 40]:
                c.changeset_2 = c.rhodecode_repo.get_changeset(diff2)
                node2 = c.changeset_2.get_node(f_path)
            else:
                c.changeset_2 = EmptyChangeset()
                node2 = FileNode('.', '', changeset=c.changeset_2)
        except RepositoryError:
            return redirect(url('files_home',
                                repo_name=c.repo_name, f_path=f_path))


        if c.action == 'download':
            diff = differ.DiffProcessor(differ.get_gitdiff(node1, node2),
                                        format='gitdiff')

            diff_name = '%s_vs_%s.diff' % (diff1, diff2)
            response.content_type = 'text/plain'
            response.content_disposition = 'attachment; filename=%s' \
                                                    % diff_name
            return diff.raw_diff()

        elif c.action == 'raw':
            diff = differ.DiffProcessor(differ.get_gitdiff(node1, node2),
                                        format='gitdiff')
            response.content_type = 'text/plain'
            return diff.raw_diff()

        elif c.action == 'diff':

            if node1.is_binary or node2.is_binary:
                c.cur_diff = _('Binary file')
            elif node1.size > self.cut_off_limit or node2.size > self.cut_off_limit:
                c.cur_diff = _('Diff is too big to display')
            else:
                diff = differ.DiffProcessor(differ.get_gitdiff(node1, node2),
                                        format='gitdiff')
                c.cur_diff = diff.as_html()
        else:

            #default option
            if node1.is_binary or node2.is_binary:
                c.cur_diff = _('Binary file')
            elif node1.size > self.cut_off_limit or node2.size > self.cut_off_limit:
                c.cur_diff = _('Diff is too big to display')
            else:
                diff = differ.DiffProcessor(differ.get_gitdiff(node1, node2),
                                        format='gitdiff')
                c.cur_diff = diff.as_html()

        if not c.cur_diff:
            c.no_changes = True
        return render('files/file_diff.html')

    def _get_history(self, repo, node, f_path):
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

        for name, chs in c.rhodecode_repo.branches.items():
            #chs = chs.split(':')[-1]
            branches_group[0].append((chs, name),)
        hist_l.append(branches_group)

        for name, chs in c.rhodecode_repo.tags.items():
            #chs = chs.split(':')[-1]
            tags_group[0].append((chs, name),)
        hist_l.append(tags_group)

        return hist_l

