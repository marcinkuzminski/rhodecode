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
from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import ChangesetStatus

log = logging.getLogger(__name__)


class ChangesetStatusModel(BaseModel):

    def __get_changeset_status(self, changeset_status):
        return self._get_instance(ChangesetStatus, changeset_status)

    def get_status(self, repo, revision):
        return 'status'
