# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.pullrequests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pull requests controller for rhodecode for initializing pull requests

    :created_on: May 7, 2012
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

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from webob.exc import HTTPNotFound

log = logging.getLogger(__name__)


class PullrequestsController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(PullrequestsController, self).__before__()

    def _get_repo_refs(self,repo):
        hist_l = []

        branches_group = ([(k, k) for k in repo.branches.keys()], _("Branches"))
        bookmarks_group = ([(k, k) for k in repo.bookmarks.keys()], _("Bookmarks"))
        tags_group = ([(k, k) for k in repo.tags.keys()], _("Tags"))

        hist_l.append(bookmarks_group)
        hist_l.append(branches_group)
        hist_l.append(tags_group)

        return hist_l

    def index(self):
        c.org_refs = self._get_repo_refs(c.rhodecode_repo)
        c.sources = []
        c.sources.append('%s/%s' % (c.rhodecode_db_repo.user.username,
                                    c.repo_name))
        return render('/pullrequests/pullrequest.html')
