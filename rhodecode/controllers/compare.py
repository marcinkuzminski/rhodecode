# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.compare
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    compare controller for pylons showing differences between two
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
import re

from webob.exc import HTTPNotFound
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.lib.vcs.exceptions import EmptyRepositoryError, RepositoryError
from rhodecode.lib.vcs.utils import safe_str
from rhodecode.lib.vcs.utils.hgcompat import scmutil
from rhodecode.lib import helpers as h
from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib import diffs, unionrepo

from rhodecode.model.db import Repository
from webob.exc import HTTPBadRequest
from rhodecode.lib.diffs import LimitedDiffContainer


log = logging.getLogger(__name__)


class CompareController(BaseRepoController):

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

    def _get_changesets(self, alias, org_repo, org_ref, other_repo, other_ref, merge):
        """
        Returns a list of changesets that can be merged from org_repo@org_ref
        to other_repo@other_ref ... and the ancestor that would be used for merge

        :param org_repo:
        :param org_ref:
        :param other_repo:
        :param other_ref:
        :param tmp:
        """

        ancestor = None

        if alias == 'hg':
            # lookup up the exact node id
            _revset_predicates = {
                    'branch': 'branch',
                    'book': 'bookmark',
                    'tag': 'tag',
                    'rev': 'id',
                }

            org_rev_spec = "max(%s(%%s))" % _revset_predicates[org_ref[0]]
            org_revs = org_repo._repo.revs(org_rev_spec, safe_str(org_ref[1]))
            org_rev = org_repo._repo[org_revs[-1] if org_revs else -1].hex()

            other_revs_spec = "max(%s(%%s))" % _revset_predicates[other_ref[0]]
            other_revs = other_repo._repo.revs(other_revs_spec, safe_str(other_ref[1]))
            other_rev = other_repo._repo[other_revs[-1] if other_revs else -1].hex()

            #case two independent repos
            if org_repo != other_repo:
                hgrepo = unionrepo.unionrepository(other_repo.baseui,
                                                   other_repo.path,
                                                   org_repo.path)
                # all the changesets we are looking for will be in other_repo,
                # so rev numbers from hgrepo can be used in other_repo

            #no remote compare do it on the same repository
            else:
                hgrepo = other_repo._repo

            if merge:
                revs = hgrepo.revs("ancestors(id(%s)) and not ancestors(id(%s)) and not id(%s)",
                                   other_rev, org_rev, org_rev)

                ancestors = hgrepo.revs("ancestor(id(%s), id(%s))", org_rev, other_rev)
                if ancestors:
                    # pick arbitrary ancestor - but there is usually only one
                    ancestor = hgrepo[ancestors[0]].hex()
            else:
                # TODO: have both + and - changesets
                revs = hgrepo.revs("id(%s) :: id(%s) - id(%s)",
                                   org_rev, other_rev, org_rev)

            changesets = [other_repo.get_changeset(rev) for rev in revs]

        elif alias == 'git':
            if org_repo != other_repo:
                raise Exception('Comparing of different GIT repositories is not'
                                'allowed. Got %s != %s' % (org_repo, other_repo))

            so, se = org_repo.run_git_command(
                'log --reverse --pretty="format: %%H" -s -p %s..%s'
                    % (org_ref[1], other_ref[1])
            )
            changesets = [org_repo.get_changeset(cs)
                          for cs in re.findall(r'[0-9a-fA-F]{40}', so)]

        return changesets, ancestor

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def index(self, org_ref_type, org_ref, other_ref_type, other_ref):
        # org_ref will be evaluated in org_repo
        org_repo = c.rhodecode_db_repo.repo_name
        org_ref = (org_ref_type, org_ref)
        # other_ref will be evaluated in other_repo
        other_ref = (other_ref_type, other_ref)
        other_repo = request.GET.get('other_repo', org_repo)
        # If merge is True:
        #   Show what org would get if merged with other:
        #   List changesets that are ancestors of other but not of org.
        #   New changesets in org is thus ignored.
        #   Diff will be from common ancestor, and merges of org to other will thus be ignored.
        # If merge is False:
        #   Make a raw diff from org to other, no matter if related or not.
        #   Changesets in one and not in the other will be ignored
        merge = bool(request.GET.get('merge'))
        # fulldiff disables cut_off_limit
        c.fulldiff = request.GET.get('fulldiff')
        # partial uses compare_cs.html template directly
        partial = request.environ.get('HTTP_X_PARTIAL_XHR')
        # as_form puts hidden input field with changeset revisions
        c.as_form = partial and request.GET.get('as_form')
        # swap url for compare_diff page - never partial and never as_form
        c.swap_url = h.url('compare_url',
            repo_name=other_repo,
            org_ref_type=other_ref[0], org_ref=other_ref[1],
            other_repo=org_repo,
            other_ref_type=org_ref[0], other_ref=org_ref[1],
            merge=merge or '')

        org_repo = Repository.get_by_repo_name(org_repo)
        other_repo = Repository.get_by_repo_name(other_repo)

        if org_repo is None:
            log.error('Could not find org repo %s' % org_repo)
            raise HTTPNotFound
        if other_repo is None:
            log.error('Could not find other repo %s' % other_repo)
            raise HTTPNotFound

        if org_repo != other_repo and h.is_git(org_repo):
            log.error('compare of two remote repos not available for GIT REPOS')
            raise HTTPNotFound

        if org_repo.scm_instance.alias != other_repo.scm_instance.alias:
            log.error('compare of two different kind of remote repos not available')
            raise HTTPNotFound

        self.__get_cs_or_redirect(rev=org_ref, repo=org_repo, partial=partial)
        self.__get_cs_or_redirect(rev=other_ref, repo=other_repo, partial=partial)

        c.org_repo = org_repo
        c.other_repo = other_repo
        c.org_ref = org_ref[1]
        c.other_ref = other_ref[1]
        c.org_ref_type = org_ref[0]
        c.other_ref_type = other_ref[0]

        c.cs_ranges, c.ancestor = self._get_changesets(org_repo.scm_instance.alias,
                                                       org_repo.scm_instance, org_ref,
                                                       other_repo.scm_instance, other_ref,
                                                       merge)

        c.statuses = c.rhodecode_db_repo.statuses([x.raw_id for x in
                                                   c.cs_ranges])
        if not c.ancestor:
            log.warning('Unable to find ancestor revision')

        if partial:
            return render('compare/compare_cs.html')

        if c.ancestor:
            assert merge
            # case we want a simple diff without incoming changesets,
            # previewing what will be merged.
            # Make the diff on the other repo (which is known to have other_ref)
            log.debug('Using ancestor %s as org_ref instead of %s'
                      % (c.ancestor, org_ref))
            org_ref = ('rev', c.ancestor)
            org_repo = other_repo

        diff_limit = self.cut_off_limit if not c.fulldiff else None

        log.debug('running diff between %s and %s in %s'
                  % (org_ref, other_ref, org_repo.scm_instance.path))
        txtdiff = org_repo.scm_instance.get_diff(rev1=safe_str(org_ref[1]), rev2=safe_str(other_ref[1]))

        diff_processor = diffs.DiffProcessor(txtdiff or '', format='gitdiff',
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
            if not st['binary']:
                c.lines_added += st['added']
                c.lines_deleted += st['deleted']
            fid = h.FID('', f['filename'])
            c.files.append([fid, f['operation'], f['filename'], f['stats']])
            htmldiff = diff_processor.as_html(enable_comments=False, parsed_lines=[f])
            c.changes[fid] = [f['operation'], f['filename'], htmldiff]

        return render('compare/compare_diff.html')
