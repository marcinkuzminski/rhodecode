from rhodecode.tests import *


class TestShortlogController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    repo_name=HG_REPO))
        # Test response...

    def test_index_git(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    repo_name=GIT_REPO))
        # Test response...

    def test_index_hg_with_filenode(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    revision='tip', f_path='/vcs/exceptions.py',
                                    repo_name=HG_REPO))
        #history commits messages
        response.mustcontain('Added exceptions module, this time for real')
        response.mustcontain('Added not implemented hg backend test case')
        response.mustcontain('Added BaseChangeset class')
        # Test response...

    def test_index_git_with_filenode(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    revision='tip', f_path='/vcs/exceptions.py',
                                    repo_name=GIT_REPO))
        #history commits messages
        response.mustcontain('Added exceptions module, this time for real')
        response.mustcontain('Added not implemented hg backend test case')
        response.mustcontain('Added BaseChangeset class')

    def test_index_hg_with_filenode_that_is_dirnode(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    revision='tip', f_path='/tests',
                                    repo_name=HG_REPO))
        self.assertEqual(response.status, '302 Found')

    def test_index_git_with_filenode_that_is_dirnode(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    revision='tip', f_path='/tests',
                                    repo_name=GIT_REPO))
        self.assertEqual(response.status, '302 Found')

    def test_index_hg_with_filenode_not_existing(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    revision='tip', f_path='/wrong_path',
                                    repo_name=HG_REPO))
        self.assertEqual(response.status, '302 Found')

    def test_index_git_with_filenode_not_existing(self):
        self.log_user()
        response = self.app.get(url(controller='shortlog', action='index',
                                    revision='tip', f_path='/wrong_path',
                                    repo_name=GIT_REPO))
        self.assertEqual(response.status, '302 Found')
