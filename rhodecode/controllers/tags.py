# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.tags
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tags controller for rhodecode
    
    :created_on: Apr 21, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
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

from pylons import tmpl_context as c

from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import OrderedDict
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)

class TagsController(BaseController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(TagsController, self).__before__()

    def index(self):
        hg_model = ScmModel()
        c.repo_info = hg_model.get_repo(c.repo_name)
        c.repo_tags = OrderedDict()
        for name, hash_ in c.repo_info.tags.items():
            c.repo_tags[name] = c.repo_info.get_changeset(hash_)

        return render('tags/tags.html')
