from rhodecode.tests import *

class TestChangelogController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO))

        self.assertTrue("""<div id="chg_20" class="container">"""
                        in response.body)
        self.assertTrue("""<input class="changeset_range" id="5e204e7583b9" """
                        """name="5e204e7583b9" type="checkbox" value="1" />"""
                        in response.body)
        self.assertTrue("""<span>commit 154: 5e204e7583b9@2010-08-10 """
                        """02:18:46</span>""" in response.body)
        self.assertTrue("""Small update at simplevcs app""" in response.body)


        self.assertTrue("""<span id="5e204e7583b9c8e7b93a020bd036564b1e"""
                        """731dae" class="changed_total tooltip" """
                        """title="Affected number of files, click to """
                        """show more details">3</span>""" in response.body)

        #pagination

        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':1})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':2})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':3})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':4})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':5})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':6})


        # Test response after pagination...
        self.assertTrue("""<input class="changeset_range" id="46ad32a4f974" """
                        """name="46ad32a4f974" type="checkbox" value="1" />"""
                        in response.body)
        self.assertTrue("""<span>commit 64: 46ad32a4f974@2010-04-20"""
                        """ 01:33:21</span>"""in response.body)

        self.assertTrue("""<span id="46ad32a4f974e45472a898c6b0acb600320"""
                        """579b1" class="changed_total tooltip" """
                        """title="Affected number of files, click to """
                        """show more details">21</span>"""in response.body)
        self.assertTrue("""<div class="message"><a href="/%s/changeset/"""
                        """46ad32a4f974e45472a898c6b0acb600320579b1">"""
                        """Merge with 2e6a2bf9356ca56df08807f4ad86d48"""
                        """0da72a8f4</a></div>""" % HG_REPO in response.body)



    #def test_index_git(self):
    #    self.log_user()
    #    response = self.app.get(url(controller='changelog', action='index', repo_name=GIT_REPO))
