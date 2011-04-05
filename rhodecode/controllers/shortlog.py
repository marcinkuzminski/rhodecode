# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.shortlog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Shortlog controller for rhodecode

    :created_on: Apr 18, 2010
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

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.helpers import RepoPage

log = logging.getLogger(__name__)


class ShortlogController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(ShortlogController, self).__before__()

    def index(self):
        p = int(request.params.get('page', 1))
        c.repo_changesets = RepoPage(c.rhodecode_repo, page=p,
                                     items_per_page=20)
        c.shortlog_data = render('shortlog/shortlog_data.html')
        if request.params.get('partial'):
            return c.shortlog_data
        r = render('shortlog/shortlog.html')
        return r
