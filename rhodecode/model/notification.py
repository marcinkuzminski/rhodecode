# -*- coding: utf-8 -*-
"""
    rhodecode.model.notification
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Model for notifications


    :created_on: Nov 20, 2011
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

import os
import logging
import traceback
import datetime

from pylons.i18n.translation import _

import rhodecode
from rhodecode.lib import helpers as h
from rhodecode.model import BaseModel
from rhodecode.model.db import Notification, User, UserNotification

log = logging.getLogger(__name__)


class NotificationModel(BaseModel):

    def __get_user(self, user):
        return self._get_instance(User, user, callback=User.get_by_username)

    def __get_notification(self, notification):
        if isinstance(notification, Notification):
            return notification
        elif isinstance(notification, int):
            return Notification.get(notification)
        else:
            if notification:
                raise Exception('notification must be int or Instance'
                                ' of Notification got %s' % type(notification))

    def create(self, created_by, subject, body, recipients=None,
               type_=Notification.TYPE_MESSAGE, with_email=True,
               email_kwargs={}):
        """

        Creates notification of given type

        :param created_by: int, str or User instance. User who created this
            notification
        :param subject:
        :param body:
        :param recipients: list of int, str or User objects, when None
            is given send to all admins
        :param type_: type of notification
        :param with_email: send email with this notification
        :param email_kwargs: additional dict to pass as args to email template
        """
        from rhodecode.lib.celerylib import tasks, run_task

        if recipients and not getattr(recipients, '__iter__', False):
            raise Exception('recipients must be a list of iterable')

        created_by_obj = self.__get_user(created_by)

        if recipients:
            recipients_objs = []
            for u in recipients:
                obj = self.__get_user(u)
                if obj:
                    recipients_objs.append(obj)
            recipients_objs = set(recipients_objs)
        else:
            # empty recipients means to all admins
            recipients_objs = User.query().filter(User.admin == True).all()

        notif = Notification.create(created_by=created_by_obj, subject=subject,
                                    body=body, recipients=recipients_objs,
                                    type_=type_)

        if with_email is False:
            return notif

        # send email with notification
        for rec in recipients_objs:
            email_subject = NotificationModel().make_description(notif, False)
            type_ = type_
            email_body = body
            kwargs = {'subject': subject, 'body': h.rst_w_mentions(body)}
            kwargs.update(email_kwargs)
            email_body_html = EmailNotificationModel()\
                                .get_email_tmpl(type_, **kwargs)
            run_task(tasks.send_email, rec.email, email_subject, email_body,
                     email_body_html)

        return notif

    def delete(self, user, notification):
        # we don't want to remove actual notification just the assignment
        try:
            notification = self.__get_notification(notification)
            user = self.__get_user(user)
            if notification and user:
                obj = UserNotification.query()\
                        .filter(UserNotification.user == user)\
                        .filter(UserNotification.notification
                                == notification)\
                        .one()
                self.sa.delete(obj)
                return True
        except Exception:
            log.error(traceback.format_exc())
            raise

    def get_for_user(self, user):
        user = self.__get_user(user)
        return user.notifications

    def mark_all_read_for_user(self, user):
        user = self.__get_user(user)
        UserNotification.query()\
            .filter(UserNotification.read==False)\
            .update({'read': True})

    def get_unread_cnt_for_user(self, user):
        user = self.__get_user(user)
        return UserNotification.query()\
                .filter(UserNotification.read == False)\
                .filter(UserNotification.user == user).count()

    def get_unread_for_user(self, user):
        user = self.__get_user(user)
        return [x.notification for x in UserNotification.query()\
                .filter(UserNotification.read == False)\
                .filter(UserNotification.user == user).all()]

    def get_user_notification(self, user, notification):
        user = self.__get_user(user)
        notification = self.__get_notification(notification)

        return UserNotification.query()\
            .filter(UserNotification.notification == notification)\
            .filter(UserNotification.user == user).scalar()

    def make_description(self, notification, show_age=True):
        """
        Creates a human readable description based on properties
        of notification object
        """

        _map = {notification.TYPE_CHANGESET_COMMENT:_('commented on commit'),
                notification.TYPE_MESSAGE:_('sent message'),
                notification.TYPE_MENTION:_('mentioned you'),
                notification.TYPE_REGISTRATION:_('registered in RhodeCode')}

        DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        tmpl = "%(user)s %(action)s %(when)s"
        if show_age:
            when = h.age(notification.created_on)
        else:
            DTF = lambda d: datetime.datetime.strftime(d, DATETIME_FORMAT)
            when = DTF(notification.created_on)
        data = dict(user=notification.created_by_user.username,
                    action=_map[notification.type_],
                    when=when)
        return tmpl % data


class EmailNotificationModel(BaseModel):

    TYPE_CHANGESET_COMMENT = Notification.TYPE_CHANGESET_COMMENT
    TYPE_PASSWORD_RESET = 'passoword_link'
    TYPE_REGISTRATION = Notification.TYPE_REGISTRATION
    TYPE_DEFAULT = 'default'

    def __init__(self):
        self._template_root = rhodecode.CONFIG['pylons.paths']['templates'][0]
        self._tmpl_lookup = rhodecode.CONFIG['pylons.app_globals'].mako_lookup

        self.email_types = {
            self.TYPE_CHANGESET_COMMENT:'email_templates/changeset_comment.html',
            self.TYPE_PASSWORD_RESET:'email_templates/password_reset.html',
            self.TYPE_REGISTRATION:'email_templates/registration.html',
            self.TYPE_DEFAULT:'email_templates/default.html'
        }

    def get_email_tmpl(self, type_, **kwargs):
        """
        return generated template for email based on given type

        :param type_:
        """

        base = self.email_types.get(type_, self.email_types[self.TYPE_DEFAULT])
        email_template = self._tmpl_lookup.get_template(base)
        # translator inject
        _kwargs = {'_':_}
        _kwargs.update(kwargs)
        log.debug('rendering tmpl %s with kwargs %s' % (base, _kwargs))
        return email_template.render(**_kwargs)
