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

from rhodecode.lib.utils2 import extract_mentioned_users, safe_unicode
from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import ChangesetComment, User, Repository, \
    Notification, PullRequest
from rhodecode.model.notification import NotificationModel

log = logging.getLogger(__name__)


class ChangesetCommentsModel(BaseModel):

    cls = ChangesetComment

    def __get_changeset_comment(self, changeset_comment):
        return self._get_instance(ChangesetComment, changeset_comment)

    def __get_pull_request(self, pull_request):
        return self._get_instance(PullRequest, pull_request)

    def _extract_mentions(self, s):
        user_objects = []
        for username in extract_mentioned_users(s):
            user_obj = User.get_by_username(username, case_insensitive=True)
            if user_obj:
                user_objects.append(user_obj)
        return user_objects

    def create(self, text, repo, user, revision=None, pull_request=None,
               f_path=None, line_no=None, status_change=None):
        """
        Creates new comment for changeset or pull request.
        IF status_change is not none this comment is associated with a
        status change of changeset or changesets associated with pull request

        :param text:
        :param repo:
        :param user:
        :param revision:
        :param pull_request:
        :param f_path:
        :param line_no:
        :param status_change:
        """
        if not text:
            return

        repo = self._get_repo(repo)
        user = self._get_user(user)
        comment = ChangesetComment()
        comment.repo = repo
        comment.author = user
        comment.text = text
        comment.f_path = f_path
        comment.line_no = line_no

        if revision:
            cs = repo.scm_instance.get_changeset(revision)
            desc = "%s - %s" % (cs.short_id, h.shorter(cs.message, 256))
            author_email = cs.author_email
            comment.revision = revision
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            comment.pull_request = pull_request
            desc = pull_request.pull_request_id
        else:
            raise Exception('Please specify revision or pull_request_id')

        self.sa.add(comment)
        self.sa.flush()

        # make notification
        line = ''
        body = text

        #changeset
        if revision:
            if line_no:
                line = _('on line %s') % line_no
            subj = safe_unicode(
                h.link_to('Re commit: %(desc)s %(line)s' % \
                          {'desc': desc, 'line': line},
                          h.url('changeset_home', repo_name=repo.repo_name,
                                revision=revision,
                                anchor='comment-%s' % comment.comment_id,
                                qualified=True,
                          )
                )
            )
            notification_type = Notification.TYPE_CHANGESET_COMMENT
            # get the current participants of this changeset
            recipients = ChangesetComment.get_users(revision=revision)
            # add changeset author if it's in rhodecode system
            recipients += [User.get_by_email(author_email)]
            email_kwargs = {
                'status_change': status_change,
            }
        #pull request
        elif pull_request:
            _url = h.url('pullrequest_show',
                repo_name=pull_request.other_repo.repo_name,
                pull_request_id=pull_request.pull_request_id,
                anchor='comment-%s' % comment.comment_id,
                qualified=True,
            )
            subj = safe_unicode(
                h.link_to('Re pull request: %(desc)s %(line)s' % \
                          {'desc': desc, 'line': line}, _url)
            )

            notification_type = Notification.TYPE_PULL_REQUEST_COMMENT
            # get the current participants of this pull request
            recipients = ChangesetComment.get_users(pull_request_id=
                                                pull_request.pull_request_id)
            # add pull request author
            recipients += [pull_request.author]

            # add the reviewers to notification
            recipients += [x.user for x in pull_request.reviewers]

            #set some variables for email notification
            email_kwargs = {
                'pr_id': pull_request.pull_request_id,
                'status_change': status_change,
                'pr_comment_url': _url,
                'pr_comment_user': h.person(user.email),
                'pr_target_repo': h.url('summary_home',
                                   repo_name=pull_request.other_repo.repo_name,
                                   qualified=True)
            }
        # create notification objects, and emails
        NotificationModel().create(
            created_by=user, subject=subj, body=body,
            recipients=recipients, type_=notification_type,
            email_kwargs=email_kwargs
        )

        mention_recipients = set(self._extract_mentions(body))\
                                .difference(recipients)
        if mention_recipients:
            email_kwargs.update({'pr_mention': True})
            subj = _('[Mention]') + ' ' + subj
            NotificationModel().create(
                created_by=user, subject=subj, body=body,
                recipients=mention_recipients,
                type_=notification_type,
                email_kwargs=email_kwargs
            )

        return comment

    def delete(self, comment):
        """
        Deletes given comment

        :param comment_id:
        """
        comment = self.__get_changeset_comment(comment)
        self.sa.delete(comment)

        return comment

    def get_comments(self, repo_id, revision=None, pull_request=None):
        """
        Get's main comments based on revision or pull_request_id

        :param repo_id:
        :type repo_id:
        :param revision:
        :type revision:
        :param pull_request:
        :type pull_request:
        """

        q = ChangesetComment.query()\
                .filter(ChangesetComment.repo_id == repo_id)\
                .filter(ChangesetComment.line_no == None)\
                .filter(ChangesetComment.f_path == None)
        if revision:
            q = q.filter(ChangesetComment.revision == revision)
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            q = q.filter(ChangesetComment.pull_request == pull_request)
        else:
            raise Exception('Please specify revision or pull_request')
        q = q.order_by(ChangesetComment.created_on)
        return q.all()

    def get_inline_comments(self, repo_id, revision=None, pull_request=None):
        q = self.sa.query(ChangesetComment)\
            .filter(ChangesetComment.repo_id == repo_id)\
            .filter(ChangesetComment.line_no != None)\
            .filter(ChangesetComment.f_path != None)\
            .order_by(ChangesetComment.comment_id.asc())\

        if revision:
            q = q.filter(ChangesetComment.revision == revision)
        elif pull_request:
            pull_request = self.__get_pull_request(pull_request)
            q = q.filter(ChangesetComment.pull_request == pull_request)
        else:
            raise Exception('Please specify revision or pull_request_id')

        comments = q.all()

        paths = defaultdict(lambda: defaultdict(list))

        for co in comments:
            paths[co.f_path][co.line_no].append(co)
        return paths.items()
