# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.bookmarks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Bookmarks controller for rhodecode

    :created_on: Dec 1, 2011
    :author: marcink
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
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

from pylons import tmpl_context as c

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.compat import OrderedDict
from webob.exc import HTTPNotFound

log = logging.getLogger(__name__)


class BookmarksController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(BookmarksController, self).__before__()

    def index(self):
        if c.rhodecode_repo.alias != 'hg':
            raise HTTPNotFound()

        c.repo_bookmarks = OrderedDict()

        bookmarks = [(name, c.rhodecode_repo.get_changeset(hash_)) for \
                 name, hash_ in c.rhodecode_repo._repo._bookmarks.items()]
        ordered_tags = sorted(bookmarks, key=lambda x: x[1].date, reverse=True)
        for name, cs_book in ordered_tags:
            c.repo_bookmarks[name] = cs_book

        return render('bookmarks/bookmarks.html')
