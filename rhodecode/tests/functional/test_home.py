from rhodecode.tests import *


class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='home', action='index'))
        #if global permission is set
        response.mustcontain('ADD REPOSITORY')
        response.mustcontain('href="/%s/summary"' % HG_REPO)

        response.mustcontain("""<img class="icon" title="Mercurial repository" """
                        """alt="Mercurial repository" src="/images/icons/hg"""
                        """icon.png"/>""")
        response.mustcontain("""<img class="icon" title="public repository" """
                        """alt="public repository" src="/images/icons/lock_"""
                        """open.png"/>""")

        response.mustcontain(
"""<a title="Marcin Kuzminski &lt;marcin@python-works.com&gt;:\n
merge" class="tooltip" href="/vcs_test_hg/changeset/27cd5cce30c96924232dffcd24178a07ffeb5dfc">r173:27cd5cce30c9</a>""")
