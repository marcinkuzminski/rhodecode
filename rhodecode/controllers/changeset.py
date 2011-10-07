# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.changeset
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    changeset controller for pylons showoing changes beetween
    revisions

    :created_on: Apr 25, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import traceback

from pylons import tmpl_context as c, url, request, response
from pylons.i18n.translation import _
from pylons.controllers.util import redirect

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.utils import EmptyChangeset
from rhodecode.lib.compat import OrderedDict

from vcs.exceptions import RepositoryError, ChangesetError, \
ChangesetDoesNotExistError
from vcs.nodes import FileNode
from vcs.utils import diffs as differ

log = logging.getLogger(__name__)


class ChangesetController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(ChangesetController, self).__before__()
        c.affected_files_cut_off = 60

    def index(self, revision):

        def wrap_to_table(str):

            return '''<table class="code-difftable">
                        <tr class="line">
                        <td class="lineno new"></td>
                        <td class="code"><pre>%s</pre></td>
                        </tr>
                      </table>''' % str

        #get ranges of revisions if preset
        rev_range = revision.split('...')[:2]

        try:
            if len(rev_range) == 2:
                rev_start = rev_range[0]
                rev_end = rev_range[1]
                rev_ranges = c.rhodecode_repo.get_changesets(start=rev_start,
                                                            end=rev_end)
            else:
                rev_ranges = [c.rhodecode_repo.get_changeset(revision)]

            c.cs_ranges = list(rev_ranges)

        except (RepositoryError, ChangesetDoesNotExistError, Exception), e:
            log.error(traceback.format_exc())
            h.flash(str(e), category='warning')
            return redirect(url('home'))

        c.changes = OrderedDict()
        c.sum_added = 0
        c.sum_removed = 0
        c.lines_added = 0
        c.lines_deleted = 0
        c.cut_off = False  # defines if cut off limit is reached

        # Iterate over ranges (default changeset view is always one changeset)
        for changeset in c.cs_ranges:
            c.changes[changeset.raw_id] = []
            try:
                changeset_parent = changeset.parents[0]
            except IndexError:
                changeset_parent = None

            #==================================================================
            # ADDED FILES
            #==================================================================
            for node in changeset.added:

                filenode_old = FileNode(node.path, '', EmptyChangeset())
                if filenode_old.is_binary or node.is_binary:
                    diff = wrap_to_table(_('binary file'))
                    st = (0, 0)
                else:
                    # in this case node.size is good parameter since those are
                    # added nodes and their size defines how many changes were
                    # made
                    c.sum_added += node.size
                    if c.sum_added < self.cut_off_limit:
                        f_gitdiff = differ.get_gitdiff(filenode_old, node)
                        d = differ.DiffProcessor(f_gitdiff, format='gitdiff')

                        st = d.stat()
                        diff = d.as_html()

                    else:
                        diff = wrap_to_table(_('Changeset is to big and '
                                               'was cut off, see raw '
                                               'changeset instead'))
                        c.cut_off = True
                        break

                cs1 = None
                cs2 = node.last_changeset.raw_id
                c.lines_added += st[0]
                c.lines_deleted += st[1]
                c.changes[changeset.raw_id].append(('added', node, diff,
                                                    cs1, cs2, st))

            #==================================================================
            # CHANGED FILES
            #==================================================================
            if not c.cut_off:
                for node in changeset.changed:
                    try:
                        filenode_old = changeset_parent.get_node(node.path)
                    except ChangesetError:
                        log.warning('Unable to fetch parent node for diff')
                        filenode_old = FileNode(node.path, '',
                                                EmptyChangeset())

                    if filenode_old.is_binary or node.is_binary:
                        diff = wrap_to_table(_('binary file'))
                        st = (0, 0)
                    else:

                        if c.sum_removed < self.cut_off_limit:
                            f_gitdiff = differ.get_gitdiff(filenode_old, node)
                            d = differ.DiffProcessor(f_gitdiff,
                                                     format='gitdiff')
                            st = d.stat()
                            if (st[0] + st[1]) * 256 > self.cut_off_limit:
                                diff = wrap_to_table(_('Diff is to big '
                                                       'and was cut off, see '
                                                       'raw diff instead'))
                            else:
                                diff = d.as_html()

                            if diff:
                                c.sum_removed += len(diff)
                        else:
                            diff = wrap_to_table(_('Changeset is to big and '
                                                   'was cut off, see raw '
                                                   'changeset instead'))
                            c.cut_off = True
                            break

                    cs1 = filenode_old.last_changeset.raw_id
                    cs2 = node.last_changeset.raw_id
                    c.lines_added += st[0]
                    c.lines_deleted += st[1]
                    c.changes[changeset.raw_id].append(('changed', node, diff,
                                                        cs1, cs2, st))

            #==================================================================
            # REMOVED FILES
            #==================================================================
            if not c.cut_off:
                for node in changeset.removed:
                    c.changes[changeset.raw_id].append(('removed', node, None,
                                                        None, None, (0, 0)))

        if len(c.cs_ranges) == 1:
            c.changeset = c.cs_ranges[0]
            c.changes = c.changes[c.changeset.raw_id]

            return render('changeset/changeset.html')
        else:
            return render('changeset/changeset_range.html')

    def raw_changeset(self, revision):

        method = request.GET.get('diff', 'show')
        try:
            c.scm_type = c.rhodecode_repo.alias
            c.changeset = c.rhodecode_repo.get_changeset(revision)
        except RepositoryError:
            log.error(traceback.format_exc())
            return redirect(url('home'))
        else:
            try:
                c.changeset_parent = c.changeset.parents[0]
            except IndexError:
                c.changeset_parent = None
            c.changes = []

            for node in c.changeset.added:
                filenode_old = FileNode(node.path, '')
                if filenode_old.is_binary or node.is_binary:
                    diff = _('binary file') + '\n'
                else:
                    f_gitdiff = differ.get_gitdiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_gitdiff,
                                                format='gitdiff').raw_diff()

                cs1 = None
                cs2 = node.last_changeset.raw_id
                c.changes.append(('added', node, diff, cs1, cs2))

            for node in c.changeset.changed:
                filenode_old = c.changeset_parent.get_node(node.path)
                if filenode_old.is_binary or node.is_binary:
                    diff = _('binary file')
                else:
                    f_gitdiff = differ.get_gitdiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_gitdiff,
                                                format='gitdiff').raw_diff()

                cs1 = filenode_old.last_changeset.raw_id
                cs2 = node.last_changeset.raw_id
                c.changes.append(('changed', node, diff, cs1, cs2))

        response.content_type = 'text/plain'

        if method == 'download':
            response.content_disposition = 'attachment; filename=%s.patch' \
                                            % revision

        c.parent_tmpl = ''.join(['# Parent  %s\n' % x.raw_id for x in
                                                 c.changeset.parents])

        c.diffs = ''
        for x in c.changes:
            c.diffs += x[2]

        return render('changeset/raw_changeset.html')
