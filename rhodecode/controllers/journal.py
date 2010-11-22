#!/usr/bin/env python
# encoding: utf-8
# journal controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
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
"""
Created on November 21, 2010
journal controller for pylons
@author: marcink
"""

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from rhodecode.lib.auth import LoginRequired
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.helpers import get_token
from rhodecode.model.db import UserLog, UserFollowing
from rhodecode.model.scm import ScmModel
import logging
from paste.httpexceptions import HTTPInternalServerError, HTTPNotFound

log = logging.getLogger(__name__)

class JournalController(BaseController):


    @LoginRequired()
    def __before__(self):
        super(JournalController, self).__before__()

    def index(self):
        # Return a rendered template

        c.following = self.sa.query(UserFollowing)\
            .filter(UserFollowing.user_id == c.rhodecode_user.user_id).all()


        c.journal = self.sa.query(UserLog)\
            .order_by(UserLog.action_date.desc())\
            .all()
        return render('/journal.html')


    def toggle_following(self):
        print c.rhodecode_user

        if request.POST.get('auth_token') == get_token():
            scm_model = ScmModel()

            user_id = request.POST.get('follows_user_id')
            if user_id:
                try:
                    scm_model.toggle_following_user(user_id,
                                                    c.rhodecode_user.user_id)
                    return 'ok'
                except:
                    raise HTTPInternalServerError()

            repo_id = request.POST.get('follows_repo_id')
            if repo_id:
                try:
                    scm_model.toggle_following_repo(repo_id,
                                                    c.rhodecode_user.user_id)
                    return 'ok'
                except:
                    raise HTTPInternalServerError()



        raise HTTPInternalServerError()
