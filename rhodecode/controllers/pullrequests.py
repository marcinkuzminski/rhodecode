# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.pullrequests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pull requests controller for rhodecode for initializing pull requests

    :created_on: May 7, 2012
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
from pylons.i18n.translation import _

from rhodecode.lib.base import BaseRepoController, render
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAnyDecorator
from rhodecode.lib import helpers as h
from rhodecode.lib import diffs
from rhodecode.model.db import User, PullRequest, Repository, ChangesetStatus
from rhodecode.model.pull_request import PullRequestModel
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from rhodecode.model.comment import ChangesetCommentsModel
from rhodecode.model.changeset_status import ChangesetStatusModel

log = logging.getLogger(__name__)


class PullrequestsController(BaseRepoController):

    @LoginRequired()
    @HasRepoPermissionAnyDecorator('repository.read', 'repository.write',
                                   'repository.admin')
    def __before__(self):
        super(PullrequestsController, self).__before__()

    def _get_repo_refs(self, repo):
        hist_l = []

        branches_group = ([('branch:%s:%s' % (k, v), k) for
                         k, v in repo.branches.iteritems()], _("Branches"))
        bookmarks_group = ([('book:%s:%s' % (k, v), k) for
                         k, v in repo.bookmarks.iteritems()], _("Bookmarks"))
        tags_group = ([('tag:%s:%s' % (k, v), k) for 
                         k, v in repo.tags.iteritems()], _("Tags"))

        hist_l.append(bookmarks_group)
        hist_l.append(branches_group)
        hist_l.append(tags_group)

        return hist_l

    def show_all(self, repo_name):
        c.pull_requests = PullRequestModel().get_all(repo_name)
        c.repo_name = repo_name
        return render('/pullrequests/pullrequest_show_all.html')

    def index(self):
        org_repo = c.rhodecode_db_repo
        c.org_refs = self._get_repo_refs(c.rhodecode_repo)
        c.org_repos = []
        c.other_repos = []
        c.org_repos.append((org_repo.repo_name, '%s/%s' % (
                                org_repo.user.username, c.repo_name))
                           )

        c.other_refs = c.org_refs
        c.other_repos.extend(c.org_repos)
        c.default_pull_request = org_repo.repo_name
        #gather forks and add to this list
        for fork in org_repo.forks:
            c.other_repos.append((fork.repo_name, '%s/%s' % (
                                    fork.user.username, fork.repo_name))
                                 )
        #add parents of this fork also
        if org_repo.parent:
            c.default_pull_request = org_repo.parent.repo_name
            c.other_repos.append((org_repo.parent.repo_name, '%s/%s' % (
                                        org_repo.parent.user.username,
                                        org_repo.parent.repo_name))
                                     )

        #TODO: maybe the owner should be default ?
        c.review_members = []
        c.available_members = []
        for u in User.query().filter(User.username != 'default').all():
            uname = u.username
            if org_repo.user == u:
                uname = _('%s (owner)' % u.username)
                # auto add owner to pull-request recipients
                c.review_members.append([u.user_id, uname])
            c.available_members.append([u.user_id, uname])
        return render('/pullrequests/pullrequest.html')

    def create(self, repo_name):
        req_p = request.POST
        org_repo = req_p['org_repo']
        org_ref = req_p['org_ref']
        other_repo = req_p['other_repo']
        other_ref = req_p['other_ref']
        revisions = req_p.getall('revisions')
        reviewers = req_p.getall('review_members')
        #TODO: wrap this into a FORM !!!

        title = req_p['pullrequest_title']
        description = req_p['pullrequest_desc']

        try:
            model = PullRequestModel()
            model.create(self.rhodecode_user.user_id, org_repo,
                         org_ref, other_repo, other_ref, revisions,
                         reviewers, title, description)
            Session.commit()
            h.flash(_('Pull request send'), category='success')
        except Exception:
            raise
            h.flash(_('Error occured during sending pull request'),
                    category='error')
            log.error(traceback.format_exc())

        return redirect(url('changelog_home', repo_name=repo_name))

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

    def _compare(self, pull_request):

        org_repo = pull_request.org_repo
        org_ref_type, org_ref_, org_ref = pull_request.org_ref.split(':')
        other_repo = pull_request.other_repo
        other_ref_type, other_ref, other_ref_ = pull_request.other_ref.split(':')

        org_ref = (org_ref_type, org_ref)
        other_ref = (other_ref_type, other_ref)

        c.org_repo = org_repo
        c.other_repo = other_repo

        discovery_data = self._get_discovery(org_repo.scm_instance,
                                           org_ref,
                                           other_repo.scm_instance,
                                           other_ref)
        c.cs_ranges = self._get_changesets(org_repo.scm_instance,
                                           org_ref,
                                           other_repo.scm_instance,
                                           other_ref,
                                           discovery_data)

        c.statuses = c.rhodecode_db_repo.statuses([x.raw_id for x in
                                                   c.cs_ranges])
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

    def show(self, repo_name, pull_request_id):
        repo_model = RepoModel()
        c.users_array = repo_model.get_users_js()
        c.users_groups_array = repo_model.get_users_groups_js()
        c.pull_request = PullRequest.get(pull_request_id)
        ##TODO: need more generic solution
        self._compare(c.pull_request)

        # inline comments
        c.inline_cnt = 0
        c.inline_comments = ChangesetCommentsModel()\
                            .get_inline_comments(c.rhodecode_db_repo.repo_id,
                                                 pull_request=pull_request_id)
        # count inline comments
        for __, lines in c.inline_comments:
            for comments in lines.values():
                c.inline_cnt += len(comments)
        # comments
        c.comments = ChangesetCommentsModel()\
                          .get_comments(c.rhodecode_db_repo.repo_id,
                                        pull_request=pull_request_id)

        # changeset(pull-request) statuse
        c.current_changeset_status = ChangesetStatusModel()\
                              .get_status(c.rhodecode_db_repo.repo_id,
                                          pull_request=pull_request_id)
        c.changeset_statuses = ChangesetStatus.STATUSES
        return render('/pullrequests/pullrequest_show.html')
