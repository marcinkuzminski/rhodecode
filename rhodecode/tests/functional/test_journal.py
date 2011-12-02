from rhodecode.tests import *
from rhodecode.model.db import UserFollowing, User, Repository
from rhodecode.lib.helpers import get_token
import datetime

class TestJournalController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='journal', action='index'))

        # Test response...
        assert """ <span id="follow_toggle_1" class="following" title="Stop following this repository""" in response.body, 'no info about stop follwoing repo id 1'

        assert """<div class="journal_day">%s</div>""" % datetime.date.today() in response.body, 'no info about action journal day'

    def test_stop_following_repository(self):
        session = self.log_user()
#        usr = self.Session.query(User).filter(User.username == 'test_admin').one()
#        repo = self.Session.query(Repository).filter(Repository.repo_name == HG_REPO).one()
#
#        followings = self.Session.query(UserFollowing)\
#            .filter(UserFollowing.user == usr)\
#            .filter(UserFollowing.follows_repository == repo).all()
#
#        assert len(followings) == 1, 'Not following any repository'
#
#        response = self.app.post(url(controller='journal',
#                                     action='toggle_following'),
#                                     {'auth_token':get_token(session),
#                                      'follows_repo_id':repo.repo_id})

    def test_start_following_repository(self):
        self.log_user()
        response = self.app.get(url(controller='journal', action='index'),)


    def __add_repo(self):
        pass

    def __remove_repo(self):
        pass
