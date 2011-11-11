# -*- coding: utf-8 -*-
"""
    rhodecode.model.comment
    ~~~~~~~~~~~~~~~~~~~~~~~

    comments model for RhodeCode
    
    :created_on: Nov 11, 2011
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
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

from rhodecode.model import BaseModel
from rhodecode.model.db import ChangesetComment

log = logging.getLogger(__name__)


class ChangesetCommentsModel(BaseModel):


    def create(self, text, repo_id, user_id, commit_id, f_path=None,
               line_no=None):
        """
        Creates new comment for changeset
        
        :param text:
        :param repo_id:
        :param user_id:
        :param commit_id:
        :param f_path:
        :param line_no:
        """

        comment = ChangesetComment()
        comment.repo_id = repo_id
        comment.user_id = user_id
        comment.commit_id = commit_id
        comment.text = text
        comment.f_path = f_path
        comment.line_no = line_no

        self.sa.add(comment)
        self.sa.commit()
        return comment

    def delete(self, comment_id):
        """
        Deletes given comment
        
        :param comment_id:
        """
        comment = ChangesetComment.get(comment_id)
        self.sa.delete(comment)
        self.sa.commit()
        return comment
