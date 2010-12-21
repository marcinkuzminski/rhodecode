from rhodecode.tests import *
from rhodecode.model.db import UserFollowing, User, Repository
from rhodecode.lib.helpers import get_token

class TestJournalController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='journal', action='index'))
        # Test response...
        assert """<div class="currently_following">
                    
                    
                        <img class="icon" title="public repository" alt="public repository" src="/images/icons/lock_open.png"/>
                      
                      <a href="/vcs_test_hg/summary">vcs_test_hg</a>
                      
                </div>""" in response.body, 'following repo list'



    def test_stop_following_repository(self):
        session = self.log_user()
#        usr = self.sa.query(User).filter(User.username == 'test_admin').one()
#        repo = self.sa.query(Repository).filter(Repository.repo_name == HG_REPO).one()
#
#        followings = self.sa.query(UserFollowing)\
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
