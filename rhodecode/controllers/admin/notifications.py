# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.notifications
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    notifications controller for RhodeCode

    :created_on: Nov 23, 2010
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
import traceback

from pylons import request
from pylons import tmpl_context as c, url
from pylons.controllers.util import redirect

from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import Notification

from rhodecode.model.notification import NotificationModel
from rhodecode.lib.auth import LoginRequired, NotAnonymous
from rhodecode.lib import helpers as h
from rhodecode.model.meta import Session


log = logging.getLogger(__name__)


class NotificationsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('notification', 'notifications', controller='_admin/notifications',
    #         path_prefix='/_admin', name_prefix='_admin_')

    @LoginRequired()
    @NotAnonymous()
    def __before__(self):
        super(NotificationsController, self).__before__()

    def index(self, format='html'):
        """GET /_admin/notifications: All items in the collection"""
        # url('notifications')
        c.user = self.rhodecode_user
        c.notifications = NotificationModel()\
                            .get_for_user(self.rhodecode_user.user_id)
        return render('admin/notifications/notifications.html')

    def mark_all_read(self):
        if request.environ.get('HTTP_X_PARTIAL_XHR'):
            nm = NotificationModel()
            # mark all read
            nm.mark_all_read_for_user(self.rhodecode_user.user_id)
            Session.commit()
            c.user = self.rhodecode_user
            c.notifications = nm.get_for_user(self.rhodecode_user.user_id)
            return render('admin/notifications/notifications_data.html')

    def create(self):
        """POST /_admin/notifications: Create a new item"""
        # url('notifications')

    def new(self, format='html'):
        """GET /_admin/notifications/new: Form to create a new item"""
        # url('new_notification')

    def update(self, notification_id):
        """PUT /_admin/notifications/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('notification', notification_id=ID),
        #           method='put')
        # url('notification', notification_id=ID)

    def delete(self, notification_id):
        """DELETE /_admin/notifications/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('notification', notification_id=ID),
        #           method='delete')
        # url('notification', notification_id=ID)

        try:
            no = Notification.get(notification_id)
            owner = lambda: (no.notifications_to_users.user.user_id
                             == c.rhodecode_user.user_id)
            if h.HasPermissionAny('hg.admin', 'repository.admin')() or owner:
                    NotificationModel().delete(c.rhodecode_user.user_id, no)
                    Session.commit()
                    return 'ok'
        except Exception:
            Session.rollback()
            log.error(traceback.format_exc())
        return 'fail'

    def show(self, notification_id, format='html'):
        """GET /_admin/notifications/id: Show a specific item"""
        # url('notification', notification_id=ID)
        c.user = self.rhodecode_user
        no = Notification.get(notification_id)

        owner = lambda: (no.notifications_to_users.user.user_id
                         == c.user.user_id)
        if no and (h.HasPermissionAny('hg.admin', 'repository.admin')() or owner):
            unotification = NotificationModel()\
                            .get_user_notification(c.user.user_id, no)

            # if this association to user is not valid, we don't want to show
            # this message
            if unotification:
                if unotification.read is False:
                    unotification.mark_as_read()
                    Session.commit()
                c.notification = no

                return render('admin/notifications/show_notification.html')

        return redirect(url('notifications'))

    def edit(self, notification_id, format='html'):
        """GET /_admin/notifications/id/edit: Form to edit an existing item"""
        # url('edit_notification', notification_id=ID)
