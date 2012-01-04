# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.tags
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tags controller for rhodecode

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

from pylons import tmpl_context as c

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.compat import OrderedDict

log = logging.getLogger(__name__)


class TagsController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(TagsController, self).__before__()

    def index(self):
        c.repo_tags = OrderedDict()

        tags = [(name, c.rhodecode_repo.get_changeset(hash_)) for \
                 name, hash_ in c.rhodecode_repo.tags.items()]
        ordered_tags = sorted(tags, key=lambda x: x[1].date, reverse=True)
        for name, cs_tag in ordered_tags:
            c.repo_tags[name] = cs_tag

        return render('tags/tags.html')
