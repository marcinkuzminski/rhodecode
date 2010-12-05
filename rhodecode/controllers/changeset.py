# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.changeset
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    changeset controller for pylons
    
    :created_on: Apr 25, 2010
    :author: marcink
    :copyright: (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>    
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

from vcs.exceptions import RepositoryError, ChangesetError
from vcs.nodes import FileNode
from vcs.utils import diffs as differ

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

        try:
            c.changeset = hg_model.get_repo(c.repo_name).get_changeset(revision)
        except RepositoryError, e:
            log.error(traceback.format_exc())
            h.flash(str(e), category='warning')
            return redirect(url('home'))
        else:
            try:
                c.changeset_old = c.changeset.parents[0]
            except IndexError:
                c.changeset_old = None
            c.changes = []

            #===================================================================
            # ADDED FILES
            #===================================================================
            c.sum_added = 0
            for node in c.changeset.added:

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
                c.changes.append(('added', node, diff, cs1, cs2))

            #===================================================================
            # CHANGED FILES
            #===================================================================
            c.sum_removed = 0
            for node in c.changeset.changed:
                try:
                    filenode_old = c.changeset_old.get_node(node.path)
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
                c.changes.append(('changed', node, diff, cs1, cs2))

            #===================================================================
            # REMOVED FILES    
            #===================================================================
            for node in c.changeset.removed:
                c.changes.append(('removed', node, None, None, None))

        return render('changeset/changeset.html')

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
                c.changeset_old = c.changeset.parents[0]
            except IndexError:
                c.changeset_old = None
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
                filenode_old = c.changeset_old.get_node(node.path)
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
