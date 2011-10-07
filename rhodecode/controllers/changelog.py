# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.changelog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    changelog controller for rhodecode

    :created_on: Apr 21, 2010
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

from mercurial import graphmod
from pylons import request, session, tmpl_context as c

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.helpers import RepoPage
from rhodecode.lib.compat import json

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

        p = int(request.params.get('page', 1))
        branch_name = request.params.get('branch', None)
        c.total_cs = len(c.rhodecode_repo)
        c.pagination = RepoPage(c.rhodecode_repo, page=p,
                                item_count=c.total_cs, items_per_page=c.size,
                                branch_name=branch_name)

        self._graph(c.rhodecode_repo, c.total_cs, c.size, p)

        return render('changelog/changelog.html')

    def changelog_details(self, cs):
        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            c.cs = c.rhodecode_repo.get_changeset(cs)
            return render('changelog/changelog_details.html')

    def _graph(self, repo, repo_size, size, p):
        """
        Generates a DAG graph for mercurial

        :param repo: repo instance
        :param size: number of commits to show
        :param p: page number
        """
        if not repo.revisions:
            c.jsdata = json.dumps([])
            return

        revcount = min(repo_size, size)
        offset = 1 if p == 1 else  ((p - 1) * revcount + 1)
        try:
            rev_end = repo.revisions.index(repo.revisions[(-1 * offset)])
        except IndexError:
            rev_end = repo.revisions.index(repo.revisions[-1])
        rev_start = max(0, rev_end - revcount)

        data = []
        rev_end += 1

        if repo.alias == 'git':
            for _ in xrange(rev_start, rev_end):
                vtx = [0, 1]
                edges = [[0, 0, 1]]
                data.append(['', vtx, edges])

        elif repo.alias == 'hg':
            revs = list(reversed(xrange(rev_start, rev_end)))
            c.dag = graphmod.colored(graphmod.dagwalker(repo._repo, revs))
            for (id, type, ctx, vtx, edges) in c.dag:
                if type != graphmod.CHANGESET:
                    continue
                data.append(['', vtx, edges])

        c.jsdata = json.dumps(data)
