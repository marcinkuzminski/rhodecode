# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.forks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    forks controller for rhodecode

    :created_on: Apr 23, 2011
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

from pylons import tmpl_context as c, request

from rhodecode.lib.helpers import Page
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.model.db import Repository, User, UserFollowing

log = logging.getLogger(__name__)


class ForksController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(ForksController, self).__before__()

    def forks(self, repo_name):
        p = int(request.params.get('page', 1))
        repo_id = c.rhodecode_db_repo.repo_id
        d = Repository.get_repo_forks(repo_id)
        c.forks_pager = Page(d, page=p, items_per_page=20)

        c.forks_data = render('/forks/forks_data.html')

        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            return c.forks_data

        return render('/forks/forks.html')
