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

    def create(self, created_by, subject, body, recipients,
               type_=Notification.TYPE_MESSAGE):
        """
        
        Creates notification of given type
        
        :param created_by: int, str or User instance. User who created this
            notification
        :param subject:
        :param body:
        :param recipients: list of int, str or User objects
        :param type_: type of notification
        """

        if not getattr(recipients, '__iter__', False):
            raise Exception('recipients must be a list of iterable')

        created_by_obj = created_by
        if not isinstance(created_by, User):
            created_by_obj = User.get(created_by)


        recipients_objs = []
        for u in recipients:
            if isinstance(u, User):
                recipients_objs.append(u)
            elif isinstance(u, basestring):
                recipients_objs.append(User.get_by_username(username=u))
            elif isinstance(u, int):
                recipients_objs.append(User.get(u))
            else:
                raise Exception('Unsupported recipient must be one of int,'
                                'str or User object')

        Notification.create(created_by=created_by_obj, subject=subject,
                            body = body, recipients = recipients_objs,
                            type_=type_)


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
