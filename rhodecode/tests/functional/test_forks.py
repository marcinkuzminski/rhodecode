from rhodecode.tests import *

from rhodecode.model.db import Repository

class TestForksController(TestController):

    def test_index(self):
        self.log_user()
        repo_name = HG_REPO
        response = self.app.get(url(controller='forks', action='forks',
                                    repo_name=repo_name))

        self.assertTrue("""There are no forks yet""" in response.body)


    def test_index_with_fork(self):
        self.log_user()

        # create a fork
        fork_name = HG_FORK
        description = 'fork of vcs test'
        repo_name = HG_REPO
        response = self.app.post(url(controller='settings',
                                     action='fork_create',
                                    repo_name=repo_name),
                                    {'fork_name':fork_name,
                                     'repo_type':'hg',
                                     'description':description,
                                     'private':'False'})

        response = self.app.get(url(controller='forks', action='forks',
                                    repo_name=repo_name))


        self.assertTrue("""<a href="/%s/summary">"""
                         """vcs_test_hg_fork</a>""" % fork_name
                         in response.body)

        #remove this fork
        response = self.app.delete(url('repo', repo_name=fork_name))

