from rhodecode.tests import *

class TestBranchesController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='branches',
                                    action='index', repo_name=HG_REPO))
        response.mustcontain("""<a href="/%s/files/27cd5cce30c96924232dffcd24178a07ffeb5dfc/">default</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/97e8b885c04894463c51898e14387d80c30ed1ee/">git</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/2e6a2bf9356ca56df08807f4ad86d480da72a8f4/">web</a>""" % HG_REPO)
