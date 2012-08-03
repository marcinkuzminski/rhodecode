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

log = logging.getLogger(__name__)


class CompareController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(CompareController, self).__before__()

    def __get_cs_or_redirect(self, rev, repo, redirect_after=True):
        """
        Safe way to get changeset if error occur it redirects to changeset with
        proper message

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
            redirect(h.url('summary_home', repo_name=repo.repo_name))

    def index(self, org_ref_type, org_ref, other_ref_type, other_ref):

        org_repo = c.rhodecode_db_repo.repo_name
        org_ref = (org_ref_type, org_ref)
        other_ref = (other_ref_type, other_ref)
        other_repo = request.GET.get('repo', org_repo)

        c.swap_url = h.url('compare_url', repo_name=other_repo,
              org_ref_type=other_ref[0], org_ref=other_ref[1],
              other_ref_type=org_ref[0], other_ref=org_ref[1],
              repo=org_repo)

        c.org_repo = org_repo = Repository.get_by_repo_name(org_repo)
        c.other_repo = other_repo = Repository.get_by_repo_name(other_repo)

        if c.org_repo is None or c.other_repo is None:
            log.error('Could not found repo %s or %s' % (org_repo, other_repo))
            raise HTTPNotFound

        if c.org_repo.scm_instance.alias != 'hg':
            log.error('Review not available for GIT REPOS')
            raise HTTPNotFound

        self.__get_cs_or_redirect(rev=org_ref, repo=org_repo)
        self.__get_cs_or_redirect(rev=other_ref, repo=other_repo)

        c.cs_ranges, discovery_data = PullRequestModel().get_compare_data(
                                       org_repo, org_ref, other_repo, other_ref
                                      )

        c.statuses = c.rhodecode_db_repo.statuses([x.raw_id for x in
                                                   c.cs_ranges])
        c.target_repo = c.repo_name
        # defines that we need hidden inputs with changesets
        c.as_form = request.GET.get('as_form', False)
        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            return render('compare/compare_cs.html')

        c.org_ref = org_ref[1]
        c.other_ref = other_ref[1]
        # diff needs to have swapped org with other to generate proper diff
        _diff = diffs.differ(other_repo, other_ref, org_repo, org_ref,
                             discovery_data)
        diff_processor = diffs.DiffProcessor(_diff, format='gitdiff')
        _parsed = diff_processor.prepare()

        c.files = []
        c.changes = {}

        for f in _parsed:
            fid = h.FID('', f['filename'])
            c.files.append([fid, f['operation'], f['filename'], f['stats']])
            diff = diff_processor.as_html(enable_comments=False, diff_lines=[f])
            c.changes[fid] = [f['operation'], f['filename'], diff]

        return render('compare/compare_diff.html')
