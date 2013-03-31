from rhodecode.tests import *


class TestFollowersController(TestController):

    def test_index_hg(self):
        self.log_user()
        repo_name = HG_REPO
        response = self.app.get(url(controller='followers',
                                    action='followers',
                                    repo_name=repo_name))

        response.mustcontain("""test_admin""")
        response.mustcontain("""Started following""")

    def test_index_git(self):
        self.log_user()
        repo_name = GIT_REPO
        response = self.app.get(url(controller='followers',
                                    action='followers',
                                    repo_name=repo_name))

        response.mustcontain("""test_admin""")
        response.mustcontain("""Started following""")
