from rhodecode.tests import *


class TestPullrequestsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='pullrequests', action='index',
                                    repo_name=HG_REPO))
