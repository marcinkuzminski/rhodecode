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
import traceback

from pylons.i18n.translation import _

from rhodecode.lib.utils2 import safe_unicode
from rhodecode.model import BaseModel
from rhodecode.model.db import ChangesetStatus, Repository, User

log = logging.getLogger(__name__)


class ChangesetStatusModel(BaseModel):

    def __get_changeset_status(self, changeset_status):
        return self._get_instance(ChangesetStatus, changeset_status)

    def __get_repo(self, repository):
        return self._get_instance(Repository, repository,
                                  callback=Repository.get_by_repo_name)

    def __get_user(self, user):
        return self._get_instance(User, user, callback=User.get_by_username)

    def get_status(self, repo, revision):
        """
        Returns status of changeset for given revision

        :param repo:
        :type repo:
        :param revision: 40char hash
        :type revision: str
        """
        repo = self.__get_repo(repo)

        status = ChangesetStatus.query()\
            .filter(ChangesetStatus.repo == repo)\
            .filter(ChangesetStatus.revision == revision).scalar()
        status = status.status if status else status
        st = status or ChangesetStatus.DEFAULT
        return str(st)

    def set_status(self, repo, revision, status, user):
        """
        Creates new status for changeset or updates the old one

        :param repo:
        :type repo:
        :param revision:
        :type revision:
        :param status:
        :type status:
        :param user:
        :type user:
        """
        repo = self.__get_repo(repo)

        cur_status = ChangesetStatus.query()\
            .filter(ChangesetStatus.repo == repo)\
            .filter(ChangesetStatus.revision == revision)\
            .scalar()
        new_status = cur_status or ChangesetStatus()
        new_status.author = self.__get_user(user)
        new_status.repo = self.__get_repo(repo)
        new_status.status = status
        new_status.revision = revision
        self.sa.add(new_status)
        return new_status

