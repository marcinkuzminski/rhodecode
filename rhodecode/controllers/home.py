# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.home
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Home controller for Rhodecode
    
    :created_on: Feb 18, 2010
    :author: marcink
    :copyright: (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>    
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
from operator import itemgetter

from pylons import tmpl_context as c, request

from rhodecode.lib.auth import LoginRequired
from rhodecode.lib.base import BaseController, render
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)

class HomeController(BaseController):

    @LoginRequired()
    def __before__(self):
        super(HomeController, self).__before__()

    def index(self):
        sortables = ['name', 'description', 'last_change', 'tip', 'owner']
        current_sort = request.GET.get('sort', 'name')
        current_sort_slug = current_sort.replace('-', '')

        if current_sort_slug not in sortables:
            c.sort_by = 'name'
            current_sort_slug = c.sort_by
        else:
            c.sort_by = current_sort
        c.sort_slug = current_sort_slug
        cached_repo_list = ScmModel().get_repos()

        sort_key = current_sort_slug + '_sort'
        if c.sort_by.startswith('-'):
            c.repos_list = sorted(cached_repo_list, key=itemgetter(sort_key),
                                  reverse=True)
        else:
            c.repos_list = sorted(cached_repo_list, key=itemgetter(sort_key),
                                  reverse=False)

        return render('/index.html')
