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

from rhodecode.model import BaseModel
from rhodecode.model.db import ChangesetStatus, PullRequest

log = logging.getLogger(__name__)


class ChangesetStatusModel(BaseModel):

    def __get_changeset_status(self, changeset_status):
        return self._get_instance(ChangesetStatus, changeset_status)

    def __get_pull_request(self, pull_request):
        return self._get_instance(PullRequest, pull_request)

    def get_status(self, repo, revision=None, pull_request=None):
        """
        Returns latest status of changeset for given revision or for given
        pull request. Statuses are versioned inside a table itself and
        version == 0 is always the current one

        :param repo:
        :type repo:
        :param revision: 40char hash or None
        :type revision: str
        :param pull_request: pull_request reference
        :type:
        """
        repo = self._get_repo(repo)

        q = ChangesetStatus.query()\
            .filter(ChangesetStatus.repo == repo)\
            .filter(ChangesetStatus.version == 0)

        if revision:
            q = q.filter(ChangesetStatus.revision == revision)
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            q = q.filter(ChangesetStatus.pull_request == pull_request)
        else:
            raise Exception('Please specify revision or pull_request')

        status = q.scalar()
        status = status.status if status else status
        st = status or ChangesetStatus.DEFAULT
        return str(st)

    def set_status(self, repo, revision, status, user, comment):
        """
        Creates new status for changeset or updates the old ones bumping their
        version, leaving the current status at

        :param repo:
        :type repo:
        :param revision:
        :type revision:
        :param status:
        :type status:
        :param user:
        :type user:
        :param comment:
        :type comment:
        """
        repo = self._get_repo(repo)

        cur_statuses = ChangesetStatus.query()\
            .filter(ChangesetStatus.repo == repo)\
            .filter(ChangesetStatus.revision == revision)\
            .all()
        if cur_statuses:
            for st in cur_statuses:
                st.version += 1
                self.sa.add(st)
        new_status = ChangesetStatus()
        new_status.author = self._get_user(user)
        new_status.repo = self._get_repo(repo)
        new_status.status = status
        new_status.revision = revision
        new_status.comment = comment
        self.sa.add(new_status)
        return new_status

