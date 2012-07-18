# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.changelog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    changelog controller for rhodecode

    :created_on: Apr 21, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
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

from pylons import request, url, session, tmpl_context as c
from pylons.controllers.util import redirect
from pylons.i18n.translation import _

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.helpers import RepoPage
from rhodecode.lib.compat import json
from rhodecode.lib.graphmod import _colored, _dagwalker
from rhodecode.lib.vcs.exceptions import RepositoryError, ChangesetDoesNotExistError

log = logging.getLogger(__name__)


class ChangelogController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(ChangelogController, self).__before__()
        c.affected_files_cut_off = 60

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
            c.size = int(session.get('changelog_size', default))
        # min size must be 1
        c.size = max(c.size, 1)
        p = int(request.params.get('page', 1))
        branch_name = request.params.get('branch', None)
        try:
            if branch_name:
                collection = [z for z in
                              c.rhodecode_repo.get_changesets(start=0,
                                                    branch_name=branch_name)]
                c.total_cs = len(collection)
            else:
                collection = c.rhodecode_repo
                c.total_cs = len(c.rhodecode_repo)

            c.pagination = RepoPage(collection, page=p, item_count=c.total_cs,
                                    items_per_page=c.size, branch=branch_name)
            collection = list(c.pagination)
            page_revisions = [x.raw_id for x in collection]
            c.comments = c.rhodecode_db_repo.get_comments(page_revisions)
            c.statuses = c.rhodecode_db_repo.statuses(page_revisions)
        except (RepositoryError, ChangesetDoesNotExistError, Exception), e:
            log.error(traceback.format_exc())
            h.flash(str(e), category='warning')
            return redirect(url('home'))

        self._graph(c.rhodecode_repo, collection, c.total_cs, c.size, p)

        c.branch_name = branch_name
        c.branch_filters = [('', _('All Branches'))] + \
            [(k, k) for k in c.rhodecode_repo.branches.keys()]

        return render('changelog/changelog.html')

    def changelog_details(self, cs):
        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            c.cs = c.rhodecode_repo.get_changeset(cs)
            return render('changelog/changelog_details.html')

    def _graph(self, repo, collection, repo_size, size, p):
        """
        Generates a DAG graph for mercurial

        :param repo: repo instance
        :param size: number of commits to show
        :param p: page number
        """
        if not collection:
            c.jsdata = json.dumps([])
            return

        data = []
        revs = [x.revision for x in collection]

        dag = _dagwalker(repo, revs, repo.alias)
        dag = _colored(dag)
        for (id, type, ctx, vtx, edges) in dag:
            data.append(['', vtx, edges])

        c.jsdata = json.dumps(data)
