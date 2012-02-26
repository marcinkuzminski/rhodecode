from rhodecode.tests import *
from rhodecode.model.db import Notification, User, UserNotification

from rhodecode.model.user import UserModel
from rhodecode.model.notification import NotificationModel
from rhodecode.model.meta import Session

class TestNotificationsController(TestController):


    def tearDown(self):
        for n in Notification.query().all():
            inst = Notification.get(n.notification_id)
            Session.delete(inst)
        Session.commit()

    def test_index(self):
        self.log_user()

        u1 = UserModel().create_or_update(username='u1', password='qweqwe',
                                               email='u1@rhodecode.org',
                                               name='u1', lastname='u1').user_id

        response = self.app.get(url('notifications'))
        self.assertTrue('''<div class="table">No notifications here yet</div>'''
                        in response.body)

        cur_user = self._get_logged_user()

        NotificationModel().create(created_by=u1, subject=u'test_notification_1',
                                   body=u'notification_1',
                                   recipients=[cur_user])
        Session.commit()
        response = self.app.get(url('notifications'))
        self.assertTrue(u'test_notification_1' in response.body)

#    def test_index_as_xml(self):
#        response = self.app.get(url('formatted_notifications', format='xml'))
#
#    def test_create(self):
#        response = self.app.post(url('notifications'))
#
#    def test_new(self):
#        response = self.app.get(url('new_notification'))
#
#    def test_new_as_xml(self):
#        response = self.app.get(url('formatted_new_notification', format='xml'))
#
#    def test_update(self):
#        response = self.app.put(url('notification', notification_id=1))
#
#    def test_update_browser_fakeout(self):
#        response = self.app.post(url('notification', notification_id=1), params=dict(_method='put'))

    def test_delete(self):
        self.log_user()
        cur_user = self._get_logged_user()

        u1 = UserModel().create_or_update(username='u1', password='qweqwe',
                                               email='u1@rhodecode.org',
                                               name='u1', lastname='u1')
        u2 = UserModel().create_or_update(username='u2', password='qweqwe',
                                               email='u2@rhodecode.org',
                                               name='u2', lastname='u2')

        # make notifications
        notification = NotificationModel().create(created_by=cur_user,
                                                  subject=u'test',
                                                  body=u'hi there',
                                                  recipients=[cur_user, u1, u2])
        Session.commit()
        u1 = User.get(u1.user_id)
        u2 = User.get(u2.user_id)

        # check DB
        get_notif = lambda un:[x.notification for x in un]
        self.assertEqual(get_notif(cur_user.notifications), [notification])
        self.assertEqual(get_notif(u1.notifications), [notification])
        self.assertEqual(get_notif(u2.notifications), [notification])
        cur_usr_id = cur_user.user_id


        response = self.app.delete(url('notification',
                                       notification_id=
                                       notification.notification_id))

        cur_user = User.get(cur_usr_id)
        self.assertEqual(cur_user.notifications, [])


#    def test_delete_browser_fakeout(self):
#        response = self.app.post(url('notification', notification_id=1), params=dict(_method='delete'))

    def test_show(self):
        self.log_user()
        cur_user = self._get_logged_user()
        u1 = UserModel().create_or_update(username='u1', password='qweqwe',
                                               email='u1@rhodecode.org',
                                               name='u1', lastname='u1')
        u2 = UserModel().create_or_update(username='u2', password='qweqwe',
                                               email='u2@rhodecode.org',
                                               name='u2', lastname='u2')

        notification = NotificationModel().create(created_by=cur_user,
                                                  subject=u'test',
                                                  body=u'hi there',
                                                  recipients=[cur_user, u1, u2])

        response = self.app.get(url('notification',
                                    notification_id=notification.notification_id))

#    def test_show_as_xml(self):
#        response = self.app.get(url('formatted_notification', notification_id=1, format='xml'))
#
#    def test_edit(self):
#        response = self.app.get(url('edit_notification', notification_id=1))
#
#    def test_edit_as_xml(self):
#        response = self.app.get(url('formatted_edit_notification', notification_id=1, format='xml'))
