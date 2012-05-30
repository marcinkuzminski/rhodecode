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
import binascii

from webob.exc import HTTPNotFound
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from rhodecode.lib import helpers as h
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
        org_repo = c.rhodecode_db_repo.repo_name

        def org_parser(org):
            _repo = org_repo
            name, val = org.split(':')
            return _repo, (name, val)

        def other_parser(other):
            _other_repo = request.GET.get('repo')
            _repo = org_repo
            name, val = other.split(':')
            if _other_repo:
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

    def _get_discovery(self, org_repo, org_ref, other_repo, other_ref):
        from mercurial import discovery
        other = org_repo._repo
        repo = other_repo._repo
        tip = other[org_ref[1]]
        log.debug('Doing discovery for %s@%s vs %s@%s' % (
                        org_repo, org_ref, other_repo, other_ref)
        )
        log.debug('Filter heads are %s[%s]' % (tip, org_ref[1]))
        tmp = discovery.findcommonincoming(
                  repo=repo,  # other_repo we check for incoming
                  remote=other,  # org_repo source for incoming
                  heads=[tip.node()],
                  force=False
        )
        return tmp

    def _get_changesets(self, org_repo, org_ref, other_repo, other_ref, tmp):
        changesets = []
        #case two independent repos
        if org_repo != other_repo:
            common, incoming, rheads = tmp

            if not incoming:
                revs = []
            else:
                revs = org_repo._repo.changelog.findmissing(common, rheads)

            for cs in reversed(map(binascii.hexlify, revs)):
                changesets.append(org_repo.get_changeset(cs))
        else:
            revs = ['ancestors(%s) and not ancestors(%s)' % (org_ref[1],
                                                             other_ref[1])]
            from mercurial import scmutil
            out = scmutil.revrange(org_repo._repo, revs)
            for cs in reversed(out):
                changesets.append(org_repo.get_changeset(cs))

        return changesets

    def index(self, ref):
        org_repo, org_ref, other_repo, other_ref = self._handle_ref(ref)

        c.swap_url = h.url('compare_home', repo_name=other_repo,
                           ref='%s...%s' % (':'.join(other_ref),
                                            ':'.join(org_ref)),
                           repo=org_repo)
        c.org_repo = org_repo = Repository.get_by_repo_name(org_repo)
        c.other_repo = other_repo = Repository.get_by_repo_name(other_repo)

        if c.org_repo is None or c.other_repo is None:
            log.error('Could not found repo %s or %s' % (org_repo, other_repo))
            raise HTTPNotFound

        discovery_data = self._get_discovery(org_repo.scm_instance,
                                           org_ref,
                                           other_repo.scm_instance,
                                           other_ref)
        c.cs_ranges = self._get_changesets(org_repo.scm_instance,
                                           org_ref,
                                           other_repo.scm_instance,
                                           other_ref,
                                           discovery_data)

        c.org_ref = org_ref[1]
        c.other_ref = other_ref[1]
        # diff needs to have swapped org with other to generate proper diff
        _diff = diffs.differ(other_repo, other_ref, org_repo, org_ref,
                             discovery_data)
        diff_processor = diffs.DiffProcessor(_diff, format='gitdiff')
        _parsed = diff_processor.prepare()

        c.files = []
        c.changes = {}
        # sort Added first then Modified last Deleted files
        sorter = lambda info: {'A': 0, 'M': 1, 'D': 2}.get(info['operation'])
        for f in sorted(_parsed, key=sorter):
            fid = h.FID('', f['filename'])
            c.files.append([fid, f['operation'], f['filename'], f['stats']])
            diff = diff_processor.as_html(enable_comments=False, diff_lines=[f])
            c.changes[fid] = [f['operation'], f['filename'], diff]

        return render('compare/compare_diff.html')
