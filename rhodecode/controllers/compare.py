# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.compare
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    compare controller for pylons showoing differences between two
    repos, branches, bookmarks or tips

    :created_on: May 6, 2012
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

from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from webob.exc import HTTPNotFound

log = logging.getLogger(__name__)


class CompareController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(CompareController, self).__before__()

    def _handle_ref(self, ref):
        """
        Parse the org...other string
        Possible formats are `(branch|book|tag):<name>...(branch|book|tag):<othername>`
        or using a repo <empty>...(repo:</rhodecode/path/to/other)


        :param ref:
        :type ref:
        """
        org_repo = c.rhodecode_repo.name

        def org_parser(org):
            _repo = org_repo
            name, val = org.split(':')
            return _repo, (name, val)

        def other_parser(other):
            _repo = org_repo
            name, val = other.split(':')
            if 'repo' in other:
                _repo = val
                name = 'branch'
                val = c.rhodecode_repo.DEFAULT_BRANCH_NAME

            return _repo, (name, val)

        if '...' in ref:
            try:
                org, other = ref.split('...')
                org_repo, org_ref = org_parser(org)
                other_repo, other_ref = other_parser(other)
                return org_repo, org_ref, other_repo, other_ref
            except:
                log.error(traceback.format_exc())

        raise HTTPNotFound

    def index(self, ref):

        org_repo, org_ref, other_repo, other_ref = self._handle_ref(ref)
        return '''
        <pre>
        REPO: %s 
        REF: %s 
        
        vs 
        
        REPO: %s 
        REF: %s        
        </pre>
        ''' % (org_repo, org_ref, other_repo, other_ref)
