from rhodecode.model.db import Repository
from rhodecode.tests import *

class TestSettingsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='settings', action='index',
                                    repo_name=HG_REPO))
        # Test response...

    def test_fork(self):
        self.log_user()
        response = self.app.get(url(controller='settings', action='fork',
                                    repo_name=HG_REPO))


    def test_fork_create(self):
        self.log_user()
        fork_name = HG_FORK
        description = 'fork of vcs test'
        repo_name = HG_REPO
        response = self.app.post(url(controller='settings', action='fork_create',
                                    repo_name=repo_name),
                                    {'fork_name':fork_name,
                                     'repo_type':'hg',
                                     'description':description,
                                     'private':'False'})

        #test if we have a message that fork is ok
        assert 'forked %s repository as %s' \
                      % (repo_name, fork_name) in response.session['flash'][0], 'No flash message about fork'

        #test if the fork was created in the database
        fork_repo = self.sa.query(Repository).filter(Repository.repo_name == fork_name).one()

        assert fork_repo.repo_name == fork_name, 'wrong name of repo name in new db fork repo'
        assert fork_repo.fork.repo_name == repo_name, 'wrong fork parrent'


        #test if fork is visible in the list ?
        response = response.follow()


        #check if fork is marked as fork
        response = self.app.get(url(controller='summary', action='index',
                                    repo_name=fork_name))

        assert 'Fork of %s' % repo_name in response.body, 'no message about that this repo is a fork'
