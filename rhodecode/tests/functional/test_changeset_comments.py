from rhodecode.tests import *
from rhodecode.model.db import ChangesetComment, Notification, User, \
    UserNotification

class TestChangeSetCommentrController(TestController):

    def setUp(self):
        for x in ChangesetComment.query().all():
            self.Session.delete(x)
        self.Session.commit()

        for x in Notification.query().all():
            self.Session.delete(x)
        self.Session.commit()

    def tearDown(self):
        for x in ChangesetComment.query().all():
            self.Session.delete(x)
        self.Session.commit()

        for x in Notification.query().all():
            self.Session.delete(x)
        self.Session.commit()

    def test_create(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        text = u'CommentOnRevision'

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
        self.assertTrue('''<div class="comments-number">%s '''
                        '''comment(s) (0 inline)</div>''' % 1 in response.body)


        self.assertEqual(Notification.query().count(), 1)
        notification = Notification.query().all()[0]

        self.assertEqual(notification.type_, Notification.TYPE_CHANGESET_COMMENT)
        self.assertTrue((u'/vcs_test_hg/changeset/27cd5cce30c96924232df'
                          'fcd24178a07ffeb5dfc#comment-1') in notification.subject)

    def test_create_inline(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        text = u'CommentOnRevision'
        f_path = 'vcs/web/simplevcs/views/repository.py'
        line = 'n1'

        params = {'text':text, 'f_path':f_path, 'line':line}
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
        self.assertTrue('''<div class="comments-number">0 comment(s)'''
                        ''' (%s inline)</div>''' % 1 in response.body)
        self.assertTrue('''<div class="inline-comment-placeholder-line"'''
                        ''' line="n1" target_id="vcswebsimplevcsviews'''
                        '''repositorypy">''' in response.body)

        self.assertEqual(Notification.query().count(), 1)
        notification = Notification.query().all()[0]

        self.assertEqual(notification.type_, Notification.TYPE_CHANGESET_COMMENT)
        self.assertTrue((u'/vcs_test_hg/changeset/27cd5cce30c96924232df'
                          'fcd24178a07ffeb5dfc#comment-1') in notification.subject)

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
        self.assertTrue('''<div class="comments-number">%s '''
                        '''comment(s) (0 inline)</div>''' % 1 in response.body)


        self.assertEqual(Notification.query().count(), 2)
        users = [x.user.username for x in UserNotification.query().all()]

        # test_regular get's notification by @mention
        self.assertEqual(sorted(users), [u'test_admin', u'test_regular'])

    def test_delete(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        text = u'CommentOnRevision'

        params = {'text':text}
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
        self.assertTrue('''<div class="comments-number">0 comment(s)'''
                        ''' (0 inline)</div>''' in response.body)
