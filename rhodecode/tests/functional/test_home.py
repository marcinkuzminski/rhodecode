from rhodecode.tests import *

class TestHomeController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='home', action='index'))
        #if global permission is set
        self.assertTrue('ADD NEW REPOSITORY' in response.body)
        self.assertTrue('href="/%s/summary"' % HG_REPO in response.body)
        # Test response...

        self.assertTrue("""<img class="icon" title="Mercurial repository" """
                        """alt="Mercurial repository" src="/images/icons/hg"""
                        """icon.png"/>""" in response.body)
        self.assertTrue("""<img class="icon" title="public repository" """
                        """alt="public repository" src="/images/icons/lock_"""
                        """open.png"/>""" in response.body)
        
        self.assertTrue("""<a title="Marcin Kuzminski &lt;marcin@python-works.com&gt;
merge" class="tooltip" href="/vcs_test_hg/changeset/27cd5cce30c96924232dffcd24178a07ffeb5dfc">r173:27cd5cce30c9</a>"""
                            in response.body)
