# -*- coding: utf-8 -*-
"""
    rhodecode.model.changeset_status
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    :created_on: Apr 30, 2012
    :author: marcink
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
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
from collections import  defaultdict

from rhodecode.model import BaseModel
from rhodecode.model.db import ChangesetStatus, PullRequest
from rhodecode.lib.exceptions import StatusChangeOnClosedPullRequestError

log = logging.getLogger(__name__)


class ChangesetStatusModel(BaseModel):

    cls = ChangesetStatus

    def __get_changeset_status(self, changeset_status):
        return self._get_instance(ChangesetStatus, changeset_status)

    def __get_pull_request(self, pull_request):
        return self._get_instance(PullRequest, pull_request)

    def _get_status_query(self, repo, revision, pull_request,
                          with_revisions=False):
        repo = self._get_repo(repo)

        q = ChangesetStatus.query()\
            .filter(ChangesetStatus.repo == repo)
        if not with_revisions:
            q = q.filter(ChangesetStatus.version == 0)

        if revision:
            q = q.filter(ChangesetStatus.revision == revision)
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            q = q.filter(ChangesetStatus.pull_request == pull_request)
        else:
            raise Exception('Please specify revision or pull_request')
        q.order_by(ChangesetStatus.version.asc())
        return q

    def calculate_status(self, statuses_by_reviewers):
        """
        approved if consensus
        (old description: leading one wins, if number of occurrences are equal than weaker wins)

        :param statuses_by_reviewers:
        """
        votes = defaultdict(int)
        reviewers_number = len(statuses_by_reviewers)
        for user, statuses in statuses_by_reviewers:
            if statuses:
                ver, latest = statuses[0]
                votes[latest.status] += 1
            else:
                votes[ChangesetStatus.DEFAULT] += 1

        if votes.get(ChangesetStatus.STATUS_APPROVED) == reviewers_number:
            return ChangesetStatus.STATUS_APPROVED
        else:
            return ChangesetStatus.STATUS_UNDER_REVIEW

    def get_statuses(self, repo, revision=None, pull_request=None,
                     with_revisions=False):
        q = self._get_status_query(repo, revision, pull_request,
                                   with_revisions)
        return q.all()

    def get_status(self, repo, revision=None, pull_request=None, as_str=True):
        """
        Returns latest status of changeset for given revision or for given
        pull request. Statuses are versioned inside a table itself and
        version == 0 is always the current one

        :param repo:
        :param revision: 40char hash or None
        :param pull_request: pull_request reference
        :param as_str: return status as string not object
        """
        q = self._get_status_query(repo, revision, pull_request)

        # need to use first here since there can be multiple statuses
        # returned from pull_request
        status = q.first()
        if as_str:
            status = status.status if status else status
            st = status or ChangesetStatus.DEFAULT
            return str(st)
        return status

    def set_status(self, repo, status, user, comment=None, revision=None,
                   pull_request=None, dont_allow_on_closed_pull_request=False):
        """
        Creates new status for changeset or updates the old ones bumping their
        version, leaving the current status at

        :param repo:
        :param revision:
        :param status:
        :param user:
        :param comment:
        :param dont_allow_on_closed_pull_request: don't allow a status change
            if last status was for pull request and it's closed. We shouldn't
            mess around this manually
        """
        repo = self._get_repo(repo)

        q = ChangesetStatus.query()
        if not comment:
            from rhodecode.model.comment import ChangesetCommentsModel
            comment = ChangesetCommentsModel().create(
                text='Auto status change to %s' % (ChangesetStatus.get_status_lbl(status)),
                repo=repo,
                user=user,
                pull_request=pull_request,
                send_email=False
            )
        if revision:
            q = q.filter(ChangesetStatus.repo == repo)
            q = q.filter(ChangesetStatus.revision == revision)
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            q = q.filter(ChangesetStatus.repo == pull_request.org_repo)
            q = q.filter(ChangesetStatus.revision.in_(pull_request.revisions))
        cur_statuses = q.all()

        #if statuses exists and last is associated with a closed pull request
        # we need to check if we can allow this status change
        if (dont_allow_on_closed_pull_request and cur_statuses
            and getattr(cur_statuses[0].pull_request, 'status', '')
                == PullRequest.STATUS_CLOSED):
            raise StatusChangeOnClosedPullRequestError(
                'Changing status on closed pull request is not allowed'
            )

        #update all current statuses with older version
        if cur_statuses:
            for st in cur_statuses:
                st.version += 1
                self.sa.add(st)

        def _create_status(user, repo, status, comment, revision, pull_request):
            new_status = ChangesetStatus()
            new_status.author = self._get_user(user)
            new_status.repo = self._get_repo(repo)
            new_status.status = status
            new_status.comment = comment
            new_status.revision = revision
            new_status.pull_request = pull_request
            return new_status

        if revision:
            new_status = _create_status(user=user, repo=repo, status=status,
                           comment=comment, revision=revision,
                           pull_request=None)
            self.sa.add(new_status)
            return new_status
        elif pull_request:
            #pull request can have more than one revision associated to it
            #we need to create new version for each one
            new_statuses = []
            repo = pull_request.org_repo
            for rev in pull_request.revisions:
                new_status = _create_status(user=user, repo=repo,
                                            status=status, comment=comment,
                                            revision=rev,
                                            pull_request=pull_request)
                new_statuses.append(new_status)
                self.sa.add(new_status)
            return new_statuses
