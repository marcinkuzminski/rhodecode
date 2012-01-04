# -*- coding: utf-8 -*-
"""
    rhodecode.model.comment
    ~~~~~~~~~~~~~~~~~~~~~~~

    comments model for RhodeCode

    :created_on: Nov 11, 2011
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
from sqlalchemy.util.compat import defaultdict

from rhodecode.lib import extract_mentioned_users
from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import ChangesetComment, User, Repository, Notification
from rhodecode.model.notification import NotificationModel

log = logging.getLogger(__name__)


class ChangesetCommentsModel(BaseModel):

    def __get_changeset_comment(self, changeset_comment):
        return self._get_instance(ChangesetComment, changeset_comment)

    def _extract_mentions(self, s):
        user_objects = []
        for username in extract_mentioned_users(s):
            user_obj = User.get_by_username(username, case_insensitive=True)
            if user_obj:
                user_objects.append(user_obj)
        return user_objects

    def create(self, text, repo_id, user_id, revision, f_path=None,
               line_no=None):
        """
        Creates new comment for changeset

        :param text:
        :param repo_id:
        :param user_id:
        :param revision:
        :param f_path:
        :param line_no:
        """
        if text:
            repo = Repository.get(repo_id)
            cs = repo.scm_instance.get_changeset(revision)
            desc = cs.message
            author = cs.author_email
            comment = ChangesetComment()
            comment.repo = repo
            comment.user_id = user_id
            comment.revision = revision
            comment.text = text
            comment.f_path = f_path
            comment.line_no = line_no

            self.sa.add(comment)
            self.sa.flush()

            # make notification
            line = ''
            if line_no:
                line = _('on line %s') % line_no
            subj = h.link_to('Re commit: %(commit_desc)s %(line)s' % \
                                    {'commit_desc': desc, 'line': line},
                             h.url('changeset_home', repo_name=repo.repo_name,
                                   revision=revision,
                                   anchor='comment-%s' % comment.comment_id,
                                   qualified=True,
                                   )
                             )
            body = text
            recipients = ChangesetComment.get_users(revision=revision)
            # add changeset author
            recipients += [User.get_by_email(author)]

            NotificationModel().create(created_by=user_id, subject=subj,
                                   body=body, recipients=recipients,
                                   type_=Notification.TYPE_CHANGESET_COMMENT)

            mention_recipients = set(self._extract_mentions(body))\
                                    .difference(recipients)
            if mention_recipients:
                subj = _('[Mention]') + ' ' + subj
                NotificationModel().create(created_by=user_id, subject=subj,
                                    body=body,
                                    recipients=mention_recipients,
                                    type_=Notification.TYPE_CHANGESET_COMMENT)

            return comment

    def delete(self, comment):
        """
        Deletes given comment

        :param comment_id:
        """
        comment = self.__get_changeset_comment(comment)
        self.sa.delete(comment)

        return comment

    def get_comments(self, repo_id, revision):
        return ChangesetComment.query()\
                .filter(ChangesetComment.repo_id == repo_id)\
                .filter(ChangesetComment.revision == revision)\
                .filter(ChangesetComment.line_no == None)\
                .filter(ChangesetComment.f_path == None).all()

    def get_inline_comments(self, repo_id, revision):
        comments = self.sa.query(ChangesetComment)\
            .filter(ChangesetComment.repo_id == repo_id)\
            .filter(ChangesetComment.revision == revision)\
            .filter(ChangesetComment.line_no != None)\
            .filter(ChangesetComment.f_path != None).all()

        paths = defaultdict(lambda: defaultdict(list))

        for co in comments:
            paths[co.f_path][co.line_no].append(co)
        return paths.items()
