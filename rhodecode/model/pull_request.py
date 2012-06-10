# -*- coding: utf-8 -*-
"""
    rhodecode.model.pull_reuquest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import PullRequest, PullRequestReviewers, Notification
from rhodecode.model.notification import NotificationModel
from rhodecode.lib.utils2 import safe_unicode

log = logging.getLogger(__name__)


class PullRequestModel(BaseModel):

    def create(self, created_by, org_repo, org_ref, other_repo,
               other_ref, revisions, reviewers, title, description=None):

        new = PullRequest()
        new.org_repo = self._get_repo(org_repo)
        new.org_ref = org_ref
        new.other_repo = self._get_repo(other_repo)
        new.other_ref = other_ref
        new.revisions = revisions
        new.title = title
        new.description = description

        self.sa.add(new)

        #members
        for member in reviewers:
            _usr = self._get_user(member)
            reviewer = PullRequestReviewers(_usr, new)
            self.sa.add(reviewer)

        #notification to reviewers
        notif = NotificationModel()
        created_by_user = self._get_user(created_by)
        subject = safe_unicode(
            h.link_to(
              _('%(user)s wants you to review pull request #%(pr_id)s') % \
                {'user': created_by_user.username,
                 'pr_id': new.pull_request_id},
              h.url('pullrequest_show', repo_name=other_repo,
                    pull_request_id=new.pull_request_id,
                    qualified=True,
              )
            )
        )
        body = description
        notif.create(created_by=created_by, subject=subject, body=body,
                     recipients=reviewers,
                     type_=Notification.TYPE_PULL_REQUEST,)

        return new
