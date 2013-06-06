from rhodecode.tests import *
from rhodecode.model.db import ChangesetComment, Notification, User, \
    UserNotification
from rhodecode.model.meta import Session


class TestChangeSetCommentsController(TestController):

    def setUp(self):
        for x in ChangesetComment.query().all():
            Session().delete(x)
        Session().commit()

        for x in Notification.query().all():
            Session().delete(x)
        Session().commit()

    def tearDown(self):
        for x in ChangesetComment.query().all():
            Session().delete(x)
        Session().commit()

        for x in Notification.query().all():
            Session().delete(x)
        Session().commit()

    def test_create(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        text = u'CommentOnRevision'

        params = {'text': text}
        response = self.app.post(url(controller='changeset', action='comment',
                                     repo_name=HG_REPO, revision=rev),
                                     params=params)
        # Test response...
        self.assertEqual(response.status, '302 Found')
        response.follow()

        response = self.app.get(url(controller='changeset', action='index',
                                repo_name=HG_REPO, revision=rev))
        # test DB
        self.assertEqual(ChangesetComment.query().count(), 1)
        response.mustcontain('''<div class="comments-number">%s comment '''
                             '''(0 inline)</div>''' % 1)

        self.assertEqual(Notification.query().count(), 1)
        self.assertEqual(ChangesetComment.query().count(), 1)

        notification = Notification.query().all()[0]

        ID = ChangesetComment.query().first().comment_id
        self.assertEqual(notification.type_,
                         Notification.TYPE_CHANGESET_COMMENT)
        sbj = (u'/vcs_test_hg/changeset/'
               '27cd5cce30c96924232dffcd24178a07ffeb5dfc#comment-%s' % ID)
        print "%s vs %s" % (sbj, notification.subject)
        self.assertTrue(sbj in notification.subject)

    def test_create_inline(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        text = u'CommentOnRevision'
        f_path = 'vcs/web/simplevcs/views/repository.py'
        line = 'n1'

        params = {'text': text, 'f_path': f_path, 'line': line}
        response = self.app.post(url(controller='changeset', action='comment',
                                     repo_name=HG_REPO, revision=rev),
                                     params=params)
        # Test response...
        self.assertEqual(response.status, '302 Found')
        response.follow()

        response = self.app.get(url(controller='changeset', action='index',
                                repo_name=HG_REPO, revision=rev))
        #test DB
        self.assertEqual(ChangesetComment.query().count(), 1)
        response.mustcontain(
            '''<div class="comments-number">0 comments'''
            ''' (%s inline)</div>''' % 1
        )
        response.mustcontain(
            '''<div style="display:none" class="inline-comment-placeholder" '''
            '''path="vcs/web/simplevcs/views/repository.py" '''
            '''target_id="vcswebsimplevcsviewsrepositorypy">'''
        )

        self.assertEqual(Notification.query().count(), 1)
        self.assertEqual(ChangesetComment.query().count(), 1)

        notification = Notification.query().all()[0]
        ID = ChangesetComment.query().first().comment_id
        self.assertEqual(notification.type_,
                         Notification.TYPE_CHANGESET_COMMENT)
        sbj = (u'/vcs_test_hg/changeset/'
               '27cd5cce30c96924232dffcd24178a07ffeb5dfc#comment-%s' % ID)
        print "%s vs %s" % (sbj, notification.subject)
        self.assertTrue(sbj in notification.subject)

    def test_create_with_mention(self):
        self.log_user()

        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        text = u'@test_regular check CommentOnRevision'

        params = {'text':text}
        response = self.app.post(url(controller='changeset', action='comment',
                                     repo_name=HG_REPO, revision=rev),
                                     params=params)
        # Test response...
        self.assertEqual(response.status, '302 Found')
        response.follow()

        response = self.app.get(url(controller='changeset', action='index',
                                repo_name=HG_REPO, revision=rev))
        # test DB
        self.assertEqual(ChangesetComment.query().count(), 1)
        response.mustcontain('''<div class="comments-number">%s '''
                             '''comment (0 inline)</div>''' % 1)

        self.assertEqual(Notification.query().count(), 2)
        users = [x.user.username for x in UserNotification.query().all()]

        # test_regular get's notification by @mention
        self.assertEqual(sorted(users), [u'test_admin', u'test_regular'])

    def test_delete(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        text = u'CommentOnRevision'

        params = {'text': text}
        response = self.app.post(url(controller='changeset', action='comment',
                                     repo_name=HG_REPO, revision=rev),
                                     params=params)

        comments = ChangesetComment.query().all()
        self.assertEqual(len(comments), 1)
        comment_id = comments[0].comment_id

        self.app.delete(url(controller='changeset',
                                    action='delete_comment',
                                    repo_name=HG_REPO,
                                    comment_id=comment_id))

        comments = ChangesetComment.query().all()
        self.assertEqual(len(comments), 0)

        response = self.app.get(url(controller='changeset', action='index',
                                repo_name=HG_REPO, revision=rev))
        response.mustcontain('''<div class="comments-number">0 comments'''
                             ''' (0 inline)</div>''')
