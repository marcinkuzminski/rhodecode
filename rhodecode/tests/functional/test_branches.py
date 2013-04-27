from rhodecode.tests import *


class TestBranchesController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='branches',
                                    action='index', repo_name=HG_REPO))
        response.mustcontain("""<a href="/%s/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/">default</a>""" % HG_REPO)

        # closed branches
        response.mustcontain("""<a href="/%s/changeset/95ca6417ec0de6ac3bd19b336d7b608f27b88711">git [closed]</a><""" % HG_REPO)
        response.mustcontain("""<a href="/%s/changeset/0dd5fd7b37a4eea4dd9b662af63cee743b4ccce2">web [closed]</a>""" % HG_REPO)

    def test_index_git(self):
        self.log_user()
        response = self.app.get(url(controller='branches',
                                    action='index', repo_name=GIT_REPO))
        response.mustcontain("""<a href="/%s/files/5f2c6ee195929b0be80749243c18121c9864a3b3/">master</a>""" % GIT_REPO)
