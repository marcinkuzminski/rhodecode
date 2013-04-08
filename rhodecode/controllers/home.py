# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.home
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Home controller for Rhodecode

    :created_on: Feb 18, 2010
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

from pylons import tmpl_context as c, request
from pylons.i18n.translation import _
from webob.exc import HTTPBadRequest
from sqlalchemy.sql.expression import func

import rhodecode
from rhodecode.lib import helpers as h
from rhodecode.lib.compat import json
from rhodecode.lib.auth import LoginRequired
from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import Repository
from rhodecode.model.repo import RepoModel


log = logging.getLogger(__name__)


class HomeController(BaseController):

    def __before__(self):
        super(HomeController, self).__before__()

    @LoginRequired()
    def index(self):
        c.groups = self.scm_model.get_repos_groups()
        c.group = None

        c.repos_list = Repository.query()\
                        .filter(Repository.group_id == None)\
                        .order_by(func.lower(Repository.repo_name))\
                        .all()

        repos_data = RepoModel().get_repos_as_dict(repos_list=c.repos_list,
                                                   admin=False)
        #json used to render the grid
        c.data = json.dumps(repos_data)

        return render('/index.html')

    @LoginRequired()
    def repo_switcher(self):
        if request.is_xhr:
            all_repos = Repository.query().order_by(Repository.repo_name).all()
            c.repos_list = self.scm_model.get_repos(all_repos,
                                                    sort_key='name_sort',
                                                    simple=True)
            return render('/repo_switcher_list.html')
        else:
            raise HTTPBadRequest()

    @LoginRequired()
    def branch_tag_switcher(self, repo_name):
        if request.is_xhr:
            c.rhodecode_db_repo = Repository.get_by_repo_name(c.repo_name)
            if c.rhodecode_db_repo:
                c.rhodecode_repo = c.rhodecode_db_repo.scm_instance
                return render('/switch_to_list.html')
        raise HTTPBadRequest()
