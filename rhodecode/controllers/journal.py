# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.journal
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Journal controller for pylons

    :created_on: Nov 21, 2010
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
from itertools import groupby

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from webhelpers.paginate import Page
from webhelpers.feedgenerator import Atom1Feed, Rss201rev2Feed

from webob.exc import HTTPBadRequest
from pylons import request, tmpl_context as c, response, url
from pylons.i18n.translation import _

import rhodecode.lib.helpers as h
from rhodecode.lib.auth import LoginRequired, NotAnonymous
from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import UserLog, UserFollowing, Repository, User
from rhodecode.model.meta import Session
from sqlalchemy.sql.expression import func
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


class JournalController(BaseController):

    def __before__(self):
        super(JournalController, self).__before__()
        self.language = 'en-us'
        self.ttl = "5"
        self.feed_nr = 20

    @LoginRequired()
    @NotAnonymous()
    def index(self):
        # Return a rendered template
        p = int(request.params.get('page', 1))

        c.user = User.get(self.rhodecode_user.user_id)
        all_repos = self.sa.query(Repository)\
                     .filter(Repository.user_id == c.user.user_id)\
                     .order_by(func.lower(Repository.repo_name)).all()

        c.user_repos = ScmModel().get_repos(all_repos)

        c.following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == self.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        journal = self._get_journal_data(c.following)

        c.journal_pager = Page(journal, page=p, items_per_page=20)

        c.journal_day_aggreagate = self._get_daily_aggregate(c.journal_pager)

        c.journal_data = render('journal/journal_data.html')
        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            return c.journal_data
        return render('journal/journal.html')

    @LoginRequired(api_access=True)
    @NotAnonymous()
    def journal_atom(self):
        """
        Produce an atom-1.0 feed via feedgenerator module
        """
        following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == self.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()
        return self._atom_feed(following, public=False)

    @LoginRequired(api_access=True)
    @NotAnonymous()
    def journal_rss(self):
        """
        Produce an rss feed via feedgenerator module
        """
        following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == self.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()
        return self._rss_feed(following, public=False)

    def _get_daily_aggregate(self, journal):
        groups = []
        for k, g in groupby(journal, lambda x: x.action_as_day):
            user_group = []
            for k2, g2 in groupby(list(g), lambda x: x.user.email):
                l = list(g2)
                user_group.append((l[0].user, l))

            groups.append((k, user_group,))

        return groups

    def _get_journal_data(self, following_repos):
        repo_ids = [x.follows_repository.repo_id for x in following_repos
                    if x.follows_repository is not None]
        user_ids = [x.follows_user.user_id for x in following_repos
                    if x.follows_user is not None]

        filtering_criterion = None

        if repo_ids and user_ids:
            filtering_criterion = or_(UserLog.repository_id.in_(repo_ids),
                        UserLog.user_id.in_(user_ids))
        if repo_ids and not user_ids:
            filtering_criterion = UserLog.repository_id.in_(repo_ids)
        if not repo_ids and user_ids:
            filtering_criterion = UserLog.user_id.in_(user_ids)
        if filtering_criterion is not None:
            journal = self.sa.query(UserLog)\
                .options(joinedload(UserLog.user))\
                .options(joinedload(UserLog.repository))\
                .filter(filtering_criterion)\
                .order_by(UserLog.action_date.desc())
        else:
            journal = []

        return journal

    @LoginRequired()
    @NotAnonymous()
    def toggle_following(self):
        cur_token = request.POST.get('auth_token')
        token = h.get_token()
        if cur_token == token:

            user_id = request.POST.get('follows_user_id')
            if user_id:
                try:
                    self.scm_model.toggle_following_user(user_id,
                                                self.rhodecode_user.user_id)
                    Session.commit()
                    return 'ok'
                except:
                    raise HTTPBadRequest()

            repo_id = request.POST.get('follows_repo_id')
            if repo_id:
                try:
                    self.scm_model.toggle_following_repo(repo_id,
                                                self.rhodecode_user.user_id)
                    Session.commit()
                    return 'ok'
                except:
                    raise HTTPBadRequest()

        log.debug('token mismatch %s vs %s' % (cur_token, token))
        raise HTTPBadRequest()

    @LoginRequired()
    def public_journal(self):
        # Return a rendered template
        p = int(request.params.get('page', 1))

        c.following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == self.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        journal = self._get_journal_data(c.following)

        c.journal_pager = Page(journal, page=p, items_per_page=20)

        c.journal_day_aggreagate = self._get_daily_aggregate(c.journal_pager)

        c.journal_data = render('journal/journal_data.html')
        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            return c.journal_data
        return render('journal/public_journal.html')

    def _atom_feed(self, repos, public=True):
        journal = self._get_journal_data(repos)
        if public:
            _link = url('public_journal_atom', qualified=True)
            _desc = '%s %s %s' % (c.rhodecode_name, _('public journal'),
                                  'atom feed')
        else:
            _link = url('journal_atom', qualified=True)
            _desc = '%s %s %s' % (c.rhodecode_name, _('journal'), 'atom feed')

        feed = Atom1Feed(title=_desc,
                         link=_link,
                         description=_desc,
                         language=self.language,
                         ttl=self.ttl)

        for entry in journal[:self.feed_nr]:
            action, action_extra, ico = h.action_parser(entry, feed=True)
            title = "%s - %s %s" % (entry.user.short_contact, action(),
                                 entry.repository.repo_name)
            desc = action_extra()
            _url = None
            if entry.repository is not None:
                _url = url('changelog_home',
                           repo_name=entry.repository.repo_name,
                           qualified=True)

            feed.add_item(title=title,
                          pubdate=entry.action_date,
                          link=_url or url('', qualified=True),
                          author_email=entry.user.email,
                          author_name=entry.user.full_contact,
                          description=desc)

        response.content_type = feed.mime_type
        return feed.writeString('utf-8')

    def _rss_feed(self, repos, public=True):
        journal = self._get_journal_data(repos)
        if public:
            _link = url('public_journal_atom', qualified=True)
            _desc = '%s %s %s' % (c.rhodecode_name, _('public journal'),
                                  'rss feed')
        else:
            _link = url('journal_atom', qualified=True)
            _desc = '%s %s %s' % (c.rhodecode_name, _('journal'), 'rss feed')

        feed = Rss201rev2Feed(title=_desc,
                         link=_link,
                         description=_desc,
                         language=self.language,
                         ttl=self.ttl)

        for entry in journal[:self.feed_nr]:
            action, action_extra, ico = h.action_parser(entry, feed=True)
            title = "%s - %s %s" % (entry.user.short_contact, action(),
                                 entry.repository.repo_name)
            desc = action_extra()
            _url = None
            if entry.repository is not None:
                _url = url('changelog_home',
                           repo_name=entry.repository.repo_name,
                           qualified=True)

            feed.add_item(title=title,
                          pubdate=entry.action_date,
                          link=_url or url('', qualified=True),
                          author_email=entry.user.email,
                          author_name=entry.user.full_contact,
                          description=desc)

        response.content_type = feed.mime_type
        return feed.writeString('utf-8')

    @LoginRequired(api_access=True)
    def public_journal_atom(self):
        """
        Produce an atom-1.0 feed via feedgenerator module
        """
        c.following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == self.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        return self._atom_feed(c.following)

    @LoginRequired(api_access=True)
    def public_journal_rss(self):
        """
        Produce an rss2 feed via feedgenerator module
        """
        c.following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == self.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        return self._rss_feed(c.following)
