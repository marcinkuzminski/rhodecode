from rhodecode.tests import *

class TestFollowersController(TestController):

    def test_index(self):
        self.log_user()
        repo_name = HG_REPO
        response = self.app.get(url(controller='followers',
                                    action='followers',
                                    repo_name=repo_name))

        self.assertTrue("""test_admin""" in response.body)
        self.assertTrue("""Started following""" in response.body)
