from rhodecode.tests import *

from rhodecode.model.db import User, Notification, UserNotification
from rhodecode.model.user import UserModel

from rhodecode.model.meta import Session
from rhodecode.model.notification import NotificationModel


class TestNotifications(BaseTestCase):

    def __init__(self, methodName='runTest'):
        Session.remove()
        self.u1 = UserModel().create_or_update(username=u'u1',
                                        password=u'qweqwe',
                                        email=u'u1@rhodecode.org',
                                        firstname=u'u1', lastname=u'u1')
        Session().commit()
        self.u1 = self.u1.user_id

        self.u2 = UserModel().create_or_update(username=u'u2',
                                        password=u'qweqwe',
                                        email=u'u2@rhodecode.org',
                                        firstname=u'u2', lastname=u'u3')
        Session().commit()
        self.u2 = self.u2.user_id

        self.u3 = UserModel().create_or_update(username=u'u3',
                                        password=u'qweqwe',
                                        email=u'u3@rhodecode.org',
                                        firstname=u'u3', lastname=u'u3')
        Session().commit()
        self.u3 = self.u3.user_id

        super(TestNotifications, self).__init__(methodName=methodName)

    def _clean_notifications(self):
        for n in Notification.query().all():
            Session().delete(n)

        Session().commit()
        self.assertEqual(Notification.query().all(), [])

    def tearDown(self):
        self._clean_notifications()

    def test_create_notification(self):
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        usrs = [self.u1, self.u2]
        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'subj', body=u'hi there',
                                           recipients=usrs)
        Session().commit()
        u1 = User.get(self.u1)
        u2 = User.get(self.u2)
        u3 = User.get(self.u3)
        notifications = Notification.query().all()
        self.assertEqual(len(notifications), 1)

        self.assertEqual(notifications[0].recipients, [u1, u2])
        self.assertEqual(notification.notification_id,
                         notifications[0].notification_id)

        unotification = UserNotification.query()\
            .filter(UserNotification.notification == notification).all()

        self.assertEqual(len(unotification), len(usrs))
        self.assertEqual(set([x.user.user_id for x in unotification]),
                         set(usrs))

    def test_user_notifications(self):
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        notification1 = NotificationModel().create(created_by=self.u1,
                                            subject=u'subj', body=u'hi there1',
                                            recipients=[self.u3])
        Session().commit()
        notification2 = NotificationModel().create(created_by=self.u1,
                                            subject=u'subj', body=u'hi there2',
                                            recipients=[self.u3])
        Session().commit()
        u3 = Session().query(User).get(self.u3)

        self.assertEqual(sorted([x.notification for x in u3.notifications]),
                         sorted([notification2, notification1]))

    def test_delete_notifications(self):
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'title', body=u'hi there3',
                                    recipients=[self.u3, self.u1, self.u2])
        Session().commit()
        notifications = Notification.query().all()
        self.assertTrue(notification in notifications)

        Notification.delete(notification.notification_id)
        Session().commit()

        notifications = Notification.query().all()
        self.assertFalse(notification in notifications)

        un = UserNotification.query().filter(UserNotification.notification
                                             == notification).all()
        self.assertEqual(un, [])

    def test_delete_association(self):

        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'title', body=u'hi there3',
                                    recipients=[self.u3, self.u1, self.u2])
        Session().commit()

        unotification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u3)\
                            .scalar()

        self.assertEqual(unotification.user_id, self.u3)

        NotificationModel().delete(self.u3,
                                   notification.notification_id)
        Session().commit()

        u3notification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u3)\
                            .scalar()

        self.assertEqual(u3notification, None)

        # notification object is still there
        self.assertEqual(Notification.query().all(), [notification])

        #u1 and u2 still have assignments
        u1notification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u1)\
                            .scalar()
        self.assertNotEqual(u1notification, None)
        u2notification = UserNotification.query()\
                            .filter(UserNotification.notification ==
                                    notification)\
                            .filter(UserNotification.user_id == self.u2)\
                            .scalar()
        self.assertNotEqual(u2notification, None)

    def test_notification_counter(self):
        self._clean_notifications()
        self.assertEqual([], Notification.query().all())
        self.assertEqual([], UserNotification.query().all())

        NotificationModel().create(created_by=self.u1,
                            subject=u'title', body=u'hi there_delete',
                            recipients=[self.u3, self.u1])
        Session().commit()

        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u1), 1)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u2), 0)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u3), 1)

        notification = NotificationModel().create(created_by=self.u1,
                                           subject=u'title', body=u'hi there3',
                                    recipients=[self.u3, self.u1, self.u2])
        Session().commit()

        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u1), 2)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u2), 1)
        self.assertEqual(NotificationModel()
                         .get_unread_cnt_for_user(self.u3), 2)
