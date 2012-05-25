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

from webob.exc import HTTPNotFound
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib import diffs

from rhodecode.model.db import Repository

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
        Possible formats are 
            `(branch|book|tag):<name>...(branch|book|tag):<othername>`

        :param ref: <orginal_reference>...<other_reference>
        :type ref: str
        """
        org_repo = c.rhodecode_repo.name

        def org_parser(org):
            _repo = org_repo
            name, val = org.split(':')
            return _repo, (name, val)

        def other_parser(other):
            _other_repo = request.GET.get('repo')
            _repo = org_repo
            name, val = other.split(':')
            if _other_repo:
                #TODO: do an actual repo loookup within rhodecode
                _repo = _other_repo

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

    def _get_changesets(self, org_repo, org_ref, other_repo, other_ref):
        changesets = []
        #case two independent repos
        if org_repo != other_repo:
            from mercurial import discovery
            import binascii
            out = discovery.findcommonoutgoing(org_repo._repo, other_repo._repo)
            for cs in map(binascii.hexlify, out.missing):
                changesets.append(org_repo.get_changeset(cs))
        else:
            for cs in map(binascii.hexlify, out):
                changesets.append(org_repo.get_changeset(cs))

        return changesets

    def index(self, ref):
        org_repo, org_ref, other_repo, other_ref = self._handle_ref(ref)

        c.org_repo = org_repo = Repository.get_by_repo_name(org_repo)
        c.other_repo = other_repo = Repository.get_by_repo_name(other_repo)

        c.cs_ranges = self._get_changesets(org_repo.scm_instance,
                                           org_ref,
                                           other_repo.scm_instance,
                                           other_ref)

        c.org_ref = org_ref[1]
        c.other_ref = other_ref[1]
        cs1 = org_repo.scm_instance.get_changeset(org_ref[1])
        cs2 = other_repo.scm_instance.get_changeset(other_ref[1])

        _diff = diffs.differ(org_repo, org_ref, other_repo, other_ref)
        diff_processor = diffs.DiffProcessor(_diff, format='gitdiff')

        diff = diff_processor.as_html(enable_comments=False)
        stats = diff_processor.stat()

        c.changes = [('change?', None, diff, cs1, cs2, stats,)]

        return render('compare/compare_diff.html')



        
