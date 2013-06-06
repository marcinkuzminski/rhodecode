# -*- coding: utf-8 -*-
"""
    rhodecode.model.pull_request
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    pull request model for RhodeCode

    :created_on: Jun 6, 2012
    :author: marcink
    :copyright: (C) 2012-2012 Marcin Kuzminski <marcin@python-works.com>
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
import datetime

from pylons.i18n.translation import _

from rhodecode.model.meta import Session
from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import PullRequest, PullRequestReviewers, Notification,\
    ChangesetStatus
from rhodecode.model.notification import NotificationModel
from rhodecode.lib.utils2 import safe_unicode


log = logging.getLogger(__name__)


class PullRequestModel(BaseModel):

    cls = PullRequest

    def __get_pull_request(self, pull_request):
        return self._get_instance(PullRequest, pull_request)

    def get_all(self, repo):
        repo = self._get_repo(repo)
        return PullRequest.query()\
                .filter(PullRequest.other_repo == repo)\
                .order_by(PullRequest.created_on.desc())\
                .all()

    def create(self, created_by, org_repo, org_ref, other_repo, other_ref,
               revisions, reviewers, title, description=None):
        from rhodecode.model.changeset_status import ChangesetStatusModel

        created_by_user = self._get_user(created_by)
        org_repo = self._get_repo(org_repo)
        other_repo = self._get_repo(other_repo)

        new = PullRequest()
        new.org_repo = org_repo
        new.org_ref = org_ref
        new.other_repo = other_repo
        new.other_ref = other_ref
        new.revisions = revisions
        new.title = title
        new.description = description
        new.author = created_by_user
        Session().add(new)
        Session().flush()
        #members
        for member in set(reviewers):
            _usr = self._get_user(member)
            reviewer = PullRequestReviewers(_usr, new)
            Session().add(reviewer)

        #reset state to under-review
        ChangesetStatusModel().set_status(
            repo=org_repo,
            status=ChangesetStatus.STATUS_UNDER_REVIEW,
            user=created_by_user,
            pull_request=new
        )
        revision_data = [(x.raw_id, x.message)
                         for x in map(org_repo.get_changeset, revisions)]
        #notification to reviewers
        pr_url = h.url('pullrequest_show', repo_name=other_repo.repo_name,
                       pull_request_id=new.pull_request_id,
                       qualified=True,
        )
        subject = safe_unicode(
            h.link_to(
              _('%(user)s wants you to review pull request #%(pr_id)s: %(pr_title)s') % \
                {'user': created_by_user.username,
                 'pr_title': new.title,
                 'pr_id': new.pull_request_id},
                pr_url
            )
        )
        body = description
        kwargs = {
            'pr_title': title,
            'pr_user_created': h.person(created_by_user.email),
            'pr_repo_url': h.url('summary_home', repo_name=other_repo.repo_name,
                                 qualified=True,),
            'pr_url': pr_url,
            'pr_revisions': revision_data
        }

        NotificationModel().create(created_by=created_by_user, subject=subject, body=body,
                                   recipients=reviewers,
                                   type_=Notification.TYPE_PULL_REQUEST, email_kwargs=kwargs)
        return new

    def update_reviewers(self, pull_request, reviewers_ids):
        reviewers_ids = set(reviewers_ids)
        pull_request = self.__get_pull_request(pull_request)
        current_reviewers = PullRequestReviewers.query()\
                            .filter(PullRequestReviewers.pull_request==
                                   pull_request)\
                            .all()
        current_reviewers_ids = set([x.user.user_id for x in current_reviewers])

        to_add = reviewers_ids.difference(current_reviewers_ids)
        to_remove = current_reviewers_ids.difference(reviewers_ids)

        log.debug("Adding %s reviewers" % to_add)
        log.debug("Removing %s reviewers" % to_remove)

        for uid in to_add:
            _usr = self._get_user(uid)
            reviewer = PullRequestReviewers(_usr, pull_request)
            Session().add(reviewer)

        for uid in to_remove:
            reviewer = PullRequestReviewers.query()\
                    .filter(PullRequestReviewers.user_id==uid,
                            PullRequestReviewers.pull_request==pull_request)\
                    .scalar()
            if reviewer:
                Session().delete(reviewer)

    def delete(self, pull_request):
        pull_request = self.__get_pull_request(pull_request)
        Session().delete(pull_request)

    def close_pull_request(self, pull_request):
        pull_request = self.__get_pull_request(pull_request)
        pull_request.status = PullRequest.STATUS_CLOSED
        pull_request.updated_on = datetime.datetime.now()
        Session().add(pull_request)
