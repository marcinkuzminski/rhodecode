# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.journal
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Journal controller for pylons
    
    :created_on: Nov 21, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
import logging

from sqlalchemy import or_
from sqlalchemy.orm import joinedload, make_transient
from webhelpers.paginate import Page
from itertools import groupby

from paste.httpexceptions import HTTPInternalServerError
from pylons import request, tmpl_context as c

from rhodecode.lib.auth import LoginRequired, NotAnonymous
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.helpers import get_token
from rhodecode.model.db import UserLog, UserFollowing

log = logging.getLogger(__name__)

class JournalController(BaseController):


    @LoginRequired()
    def __before__(self):
        super(JournalController, self).__before__()

    @NotAnonymous()
    def index(self):
        # Return a rendered template
        p = int(request.params.get('page', 1))

        c.following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == c.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        journal = self._get_journal_data(c.following)

        c.journal_pager = Page(journal, page=p, items_per_page=20)

        c.journal_day_aggreagate = self._get_daily_aggregate(c.journal_pager)

        c.journal_data = render('journal/journal_data.html')
        if request.params.get('partial'):
            return c.journal_data
        return render('journal/journal.html')


    def _get_daily_aggregate(self, journal):
        groups = []
        for k, g in groupby(journal, lambda x:x.action_as_day):
            user_group = []
            for k2, g2 in groupby(list(g), lambda x:x.user.email):
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

    @NotAnonymous()
    def toggle_following(self):
        cur_token = request.POST.get('auth_token')
        token = get_token()
        if cur_token == token:

            user_id = request.POST.get('follows_user_id')
            if user_id:
                try:
                    self.scm_model.toggle_following_user(user_id,
                                                    c.rhodecode_user.user_id)
                    return 'ok'
                except:
                    raise HTTPInternalServerError()

            repo_id = request.POST.get('follows_repo_id')
            if repo_id:
                try:
                    self.scm_model.toggle_following_repo(repo_id,
                                                    c.rhodecode_user.user_id)
                    return 'ok'
                except:
                    raise HTTPInternalServerError()


        log.debug('token mismatch %s vs %s', cur_token, token)
        raise HTTPInternalServerError()




    def public_journal(self):
        # Return a rendered template
        p = int(request.params.get('page', 1))

        c.following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == c.rhodecode_user.user_id)\
            .options(joinedload(UserFollowing.follows_repository))\
            .all()

        journal = self._get_journal_data(c.following)

        c.journal_pager = Page(journal, page=p, items_per_page=20)

        c.journal_day_aggreagate = self._get_daily_aggregate(c.journal_pager)

        c.journal_data = render('journal/journal_data.html')
        if request.params.get('partial'):
            return c.journal_data
        return render('journal/public_journal.html')
