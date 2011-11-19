# -*- coding: utf-8 -*-
"""
    rhodecode.model.notification
    ~~~~~~~~~~~~~~

    Model for notifications
    
    
    :created_on: Nov 20, 2011
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

from pylons.i18n.translation import _

from rhodecode.lib import safe_unicode
from rhodecode.lib.caching_query import FromCache

from rhodecode.model import BaseModel
from rhodecode.model.db import Notification, User, UserNotification


class NotificationModel(BaseModel):

    def create(self, subject, body, recipients):

        if not getattr(recipients, '__iter__', False):
            raise Exception('recipients must be a list of iterable')

        for x in recipients:
            if not isinstance(x, User):
                raise Exception('recipient is not instance of %s got %s' % \
                                (User, type(x)))


        Notification.create(subject, body, recipients)


    def get_for_user(self, user_id):
        return User.get(user_id).notifications

    def get_unread_cnt_for_user(self, user_id):
        return UserNotification.query()\
                .filter(UserNotification.sent_on == None)\
                .filter(UserNotification.user_id == user_id).count()

    def get_unread_for_user(self, user_id):
        return [x.notification for x in UserNotification.query()\
                .filter(UserNotification.sent_on == None)\
                .filter(UserNotification.user_id == user_id).all()]
