from rhodecode.tests import *


class TestChangelogController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO))

        response.mustcontain('''id="chg_20" class="container tablerow1"''')
        response.mustcontain(
            """<input class="changeset_range" """
            """id="5e204e7583b9c8e7b93a020bd036564b1e731dae" """
            """name="5e204e7583b9c8e7b93a020bd036564b1e731dae" """
            """type="checkbox" value="1" />"""
        )

        response.mustcontain(
            """<span class="changeset_hash">r154:5e204e7583b9</span>"""
        )

        response.mustcontain("""Small update at simplevcs app""")

#        response.mustcontain(
#            """<div id="changed_total_5e204e7583b9c8e7b93a020bd036564b1e731dae" """
#            """style="float:right;" class="changed_total tooltip" """
#            """title="Affected number of files, click to show """
#            """more details">3</div>"""
#        )

    def test_index_pagination_hg(self):
        self.log_user()
        #pagination
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page': 1})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page': 2})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page': 3})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page': 4})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page': 5})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page': 6})

        # Test response after pagination...
        response.mustcontain(
            """<input class="changeset_range" """
            """id="46ad32a4f974e45472a898c6b0acb600320579b1" """
            """name="46ad32a4f974e45472a898c6b0acb600320579b1" """
            """type="checkbox" value="1" />"""
        )

        response.mustcontain(
            """<span class="changeset_hash">r64:46ad32a4f974</span>"""
        )

#        response.mustcontain(
#            """<div id="changed_total_46ad32a4f974e45472a898c6b0acb600320579b1" """
#            """style="float:right;" class="changed_total tooltip" """
#            """title="Affected number of files, click to show """
#            """more details">21</div>"""
#        )
#
#        response.mustcontain(
#            """<a href="/%s/changeset/"""
#            """46ad32a4f974e45472a898c6b0acb600320579b1" """
#            """title="Merge with 2e6a2bf9356ca56df08807f4ad86d480da72a8f4">"""
#            """46ad32a4f974</a>""" % HG_REPO
#        )

    def test_index_git(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=GIT_REPO))

        response.mustcontain('''id="chg_20" class="container tablerow1"''')
        response.mustcontain(
            """<input class="changeset_range" """
            """id="95f9a91d775b0084b2368ae7779e44931c849c0e" """
            """name="95f9a91d775b0084b2368ae7779e44931c849c0e" """
            """type="checkbox" value="1" />"""
        )

        response.mustcontain(
            """<span class="changeset_hash">r613:95f9a91d775b</span>"""
        )

        response.mustcontain("""fixing stupid typo in context for mercurial""")

#        response.mustcontain(
#            """<div id="changed_total_5e204e7583b9c8e7b93a020bd036564b1e731dae" """
#            """style="float:right;" class="changed_total tooltip" """
#            """title="Affected number of files, click to show """
#            """more details">3</div>"""
#        )

    def test_index_pagination_git(self):
        self.log_user()
        #pagination
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=GIT_REPO), {'page': 1})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=GIT_REPO), {'page': 2})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=GIT_REPO), {'page': 3})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=GIT_REPO), {'page': 4})
        self.app.get(url(controller='changelog', action='index',
                                    repo_name=GIT_REPO), {'page': 5})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=GIT_REPO), {'page': 6})

        # Test response after pagination...
        response.mustcontain(
            """<input class="changeset_range" """
            """id="636ed213f2f11ef91071b9c24f2d5e6bd01a6ed5" """
            """name="636ed213f2f11ef91071b9c24f2d5e6bd01a6ed5" """
            """type="checkbox" value="1" />"""
        )

        response.mustcontain(
            """<span class="changeset_hash">r515:636ed213f2f1</span>"""
        )

    def test_index_hg_with_filenode(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    revision='tip', f_path='/vcs/exceptions.py',
                                    repo_name=HG_REPO))
        #history commits messages
        response.mustcontain('Added exceptions module, this time for real')
        response.mustcontain('Added not implemented hg backend test case')
        response.mustcontain('Added BaseChangeset class')
        # Test response...

    def test_index_git_with_filenode(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    revision='tip', f_path='/vcs/exceptions.py',
                                    repo_name=GIT_REPO))
        #history commits messages
        response.mustcontain('Added exceptions module, this time for real')
        response.mustcontain('Added not implemented hg backend test case')
        response.mustcontain('Added BaseChangeset class')

    def test_index_hg_with_filenode_that_is_dirnode(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    revision='tip', f_path='/tests',
                                    repo_name=HG_REPO))
        self.assertEqual(response.status, '302 Found')

    def test_index_git_with_filenode_that_is_dirnode(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    revision='tip', f_path='/tests',
                                    repo_name=GIT_REPO))
        self.assertEqual(response.status, '302 Found')

    def test_index_hg_with_filenode_not_existing(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    revision='tip', f_path='/wrong_path',
                                    repo_name=HG_REPO))
        self.assertEqual(response.status, '302 Found')

    def test_index_git_with_filenode_not_existing(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    revision='tip', f_path='/wrong_path',
                                    repo_name=GIT_REPO))
        self.assertEqual(response.status, '302 Found')
