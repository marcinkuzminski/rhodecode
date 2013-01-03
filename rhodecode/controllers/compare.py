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
from pylons.i18n.translation import _

from rhodecode.lib.vcs.exceptions import EmptyRepositoryError, RepositoryError
from rhodecode.lib import helpers as h
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib import diffs

from rhodecode.model.db import Repository
from rhodecode.model.pull_request import PullRequestModel
from webob.exc import HTTPBadRequest
from rhodecode.lib.utils2 import str2bool
from rhodecode.lib.diffs import LimitedDiffContainer
from rhodecode.lib.vcs.backends.base import EmptyChangeset

log = logging.getLogger(__name__)


class CompareController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(CompareController, self).__before__()

    def __get_cs_or_redirect(self, rev, repo, redirect_after=True,
                             partial=False):
        """
        Safe way to get changeset if error occur it redirects to changeset with
        proper message. If partial is set then don't do redirect raise Exception
        instead

        :param rev: revision to fetch
        :param repo: repo instance
        """

        try:
            type_, rev = rev
            return repo.scm_instance.get_changeset(rev)
        except EmptyRepositoryError, e:
            if not redirect_after:
                return None
            h.flash(h.literal(_('There are no changesets yet')),
                    category='warning')
            redirect(url('summary_home', repo_name=repo.repo_name))

        except RepositoryError, e:
            log.error(traceback.format_exc())
            h.flash(str(e), category='warning')
            if not partial:
                redirect(h.url('summary_home', repo_name=repo.repo_name))
            raise HTTPBadRequest()

    def index(self, org_ref_type, org_ref, other_ref_type, other_ref):

        org_repo = c.rhodecode_db_repo.repo_name
        org_ref = (org_ref_type, org_ref)
        other_ref = (other_ref_type, other_ref)
        other_repo = request.GET.get('repo', org_repo)
        incoming_changesets = str2bool(request.GET.get('bundle', False))
        c.fulldiff = fulldiff = request.GET.get('fulldiff')
        rev_start = request.GET.get('rev_start')
        rev_end = request.GET.get('rev_end')

        c.swap_url = h.url('compare_url', repo_name=other_repo,
              org_ref_type=other_ref[0], org_ref=other_ref[1],
              other_ref_type=org_ref[0], other_ref=org_ref[1],
              repo=org_repo, as_form=request.GET.get('as_form'),
              bundle=incoming_changesets)

        c.org_repo = org_repo = Repository.get_by_repo_name(org_repo)
        c.other_repo = other_repo = Repository.get_by_repo_name(other_repo)

        if c.org_repo is None:
            log.error('Could not find org repo %s' % org_repo)
            raise HTTPNotFound
        if c.other_repo is None:
            log.error('Could not find other repo %s' % other_repo)
            raise HTTPNotFound

        if c.org_repo != c.other_repo and h.is_git(c.rhodecode_repo):
            log.error('compare of two remote repos not available for GIT REPOS')
            raise HTTPNotFound

        if c.org_repo.scm_instance.alias != c.other_repo.scm_instance.alias:
            log.error('compare of two different kind of remote repos not available')
            raise HTTPNotFound

        partial = request.environ.get('HTTP_X_PARTIAL_XHR')
        self.__get_cs_or_redirect(rev=org_ref, repo=org_repo, partial=partial)
        self.__get_cs_or_redirect(rev=other_ref, repo=other_repo, partial=partial)

        if rev_start and rev_end:
            #replace our org_ref with given CS
            org_ref = ('rev', rev_start)
            other_ref = ('rev', rev_end)

        c.cs_ranges, discovery_data = PullRequestModel().get_compare_data(
                                    org_repo, org_ref, other_repo, other_ref,
                                    )

        c.statuses = c.rhodecode_db_repo.statuses([x.raw_id for x in
                                                   c.cs_ranges])
        c.target_repo = c.repo_name
        # defines that we need hidden inputs with changesets
        c.as_form = request.GET.get('as_form', False)
        if partial:
            return render('compare/compare_cs.html')

        c.org_ref = org_ref[1]
        c.other_ref = other_ref[1]

        if not incoming_changesets and c.cs_ranges and c.org_repo != c.other_repo:
            # case we want a simple diff without incoming changesets, just
            # for review purposes. Make the diff on the forked repo, with
            # revision that is common ancestor
            _org_ref = org_ref
            org_ref = ('rev', getattr(c.cs_ranges[0].parents[0]
                                      if c.cs_ranges[0].parents
                                      else EmptyChangeset(), 'raw_id'))
            log.debug('Changed org_ref from %s to %s' % (_org_ref, org_ref))
            other_repo = org_repo

        diff_limit = self.cut_off_limit if not fulldiff else None

        _diff = diffs.differ(org_repo, org_ref, other_repo, other_ref,
                             discovery_data,
                             remote_compare=incoming_changesets)

        diff_processor = diffs.DiffProcessor(_diff or '', format='gitdiff',
                                             diff_limit=diff_limit)
        _parsed = diff_processor.prepare()

        c.limited_diff = False
        if isinstance(_parsed, LimitedDiffContainer):
            c.limited_diff = True

        c.files = []
        c.changes = {}
        c.lines_added = 0
        c.lines_deleted = 0
        for f in _parsed:
            st = f['stats']
            if st[0] != 'b':
                c.lines_added += st[0]
                c.lines_deleted += st[1]
            fid = h.FID('', f['filename'])
            c.files.append([fid, f['operation'], f['filename'], f['stats']])
            diff = diff_processor.as_html(enable_comments=False, parsed_lines=[f])
            c.changes[fid] = [f['operation'], f['filename'], diff]

        return render('compare/compare_diff.html')
