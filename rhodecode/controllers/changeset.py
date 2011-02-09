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
import traceback

from pylons import tmpl_context as c, url, request, response
from pylons.i18n.translation import _
from pylons.controllers.util import redirect

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import EmptyChangeset
from rhodecode.model.scm import ScmModel

from vcs.exceptions import RepositoryError, ChangesetError, \
ChangesetDoesNotExistError
from vcs.nodes import FileNode
from vcs.utils import diffs as differ
from vcs.utils.ordered_dict import OrderedDict

log = logging.getLogger(__name__)

class ChangesetController(BaseController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(ChangesetController, self).__before__()

    def index(self, revision):
        hg_model = ScmModel()

        def wrap_to_table(str):

            return '''<table class="code-difftable">
                        <tr class="line">
                        <td class="lineno new"></td>
                        <td class="code"><pre>%s</pre></td>
                        </tr>
                      </table>''' % str

        #get ranges of revisions if preset
        rev_range = revision.split('...')[:2]
        range_limit = 50
        try:
            repo = hg_model.get_repo(c.repo_name)
            if len(rev_range) == 2:
                rev_start = rev_range[0]
                rev_end = rev_range[1]
                rev_ranges = repo.get_changesets_ranges(rev_start, rev_end,
                                                       range_limit)
            else:
                rev_ranges = [repo.get_changeset(revision)]

            c.cs_ranges = list(rev_ranges)

        except (RepositoryError, ChangesetDoesNotExistError, Exception), e:
            log.error(traceback.format_exc())
            h.flash(str(e), category='warning')
            return redirect(url('home'))

        c.changes = OrderedDict()
        c.sum_added = 0
        c.sum_removed = 0


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
                else:
                    c.sum_added += node.size
                    if c.sum_added < self.cut_off_limit:
                        f_udiff = differ.get_udiff(filenode_old, node)
                        diff = differ.DiffProcessor(f_udiff).as_html()

                    else:
                        diff = wrap_to_table(_('Changeset is to big and was cut'
                                            ' off, see raw changeset instead'))

                cs1 = None
                cs2 = node.last_changeset.raw_id
                c.changes[changeset.raw_id].append(('added', node, diff, cs1, cs2))

            #==================================================================
            # CHANGED FILES
            #==================================================================
            for node in changeset.changed:
                try:
                    filenode_old = changeset_parent.get_node(node.path)
                except ChangesetError:
                    filenode_old = FileNode(node.path, '', EmptyChangeset())

                if filenode_old.is_binary or node.is_binary:
                    diff = wrap_to_table(_('binary file'))
                else:

                    if c.sum_removed < self.cut_off_limit:
                        f_udiff = differ.get_udiff(filenode_old, node)
                        diff = differ.DiffProcessor(f_udiff).as_html()
                        if diff:
                            c.sum_removed += len(diff)
                    else:
                        diff = wrap_to_table(_('Changeset is to big and was cut'
                                            ' off, see raw changeset instead'))


                cs1 = filenode_old.last_changeset.raw_id
                cs2 = node.last_changeset.raw_id
                c.changes[changeset.raw_id].append(('changed', node, diff, cs1, cs2))

            #==================================================================
            # REMOVED FILES    
            #==================================================================
            for node in changeset.removed:
                c.changes[changeset.raw_id].append(('removed', node, None, None, None))

        if len(c.cs_ranges) == 1:
            c.changeset = c.cs_ranges[0]
            c.changes = c.changes[c.changeset.raw_id]

            return render('changeset/changeset.html')
        else:
            return render('changeset/changeset_range.html')

    def raw_changeset(self, revision):

        hg_model = ScmModel()
        method = request.GET.get('diff', 'show')
        try:
            r = hg_model.get_repo(c.repo_name)
            c.scm_type = r.alias
            c.changeset = r.get_changeset(revision)
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
                    f_udiff = differ.get_udiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_udiff).raw_diff()

                cs1 = None
                cs2 = node.last_changeset.raw_id
                c.changes.append(('added', node, diff, cs1, cs2))

            for node in c.changeset.changed:
                filenode_old = c.changeset_parent.get_node(node.path)
                if filenode_old.is_binary or node.is_binary:
                    diff = _('binary file')
                else:
                    f_udiff = differ.get_udiff(filenode_old, node)
                    diff = differ.DiffProcessor(f_udiff).raw_diff()

                cs1 = filenode_old.last_changeset.raw_id
                cs2 = node.last_changeset.raw_id
                c.changes.append(('changed', node, diff, cs1, cs2))

        response.content_type = 'text/plain'

        if method == 'download':
            response.content_disposition = 'attachment; filename=%s.patch' % revision

        parent = True if len(c.changeset.parents) > 0 else False
        c.parent_tmpl = 'Parent  %s' % c.changeset.parents[0].raw_id if parent else ''

        c.diffs = ''
        for x in c.changes:
            c.diffs += x[2]

        return render('changeset/raw_changeset.html')
