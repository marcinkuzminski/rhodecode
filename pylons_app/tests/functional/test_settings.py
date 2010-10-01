from pylons_app.model.db import Repository
from pylons_app.tests import *

class TestSettingsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='settings', action='index',
                                    repo_name='vcs_test'))
        # Test response...
    
    def test_fork(self):
        self.log_user()
        response = self.app.get(url(controller='settings', action='fork',
                                    repo_name='vcs_test'))
        

    def test_fork_create(self):
        self.log_user()
        fork_name = 'vcs_test_fork'
        description = 'fork of vcs test'
        repo_name = 'vcs_test'
        response = self.app.post(url(controller='settings', action='fork_create',
                                    repo_name=repo_name),
                                    {'fork_name':fork_name,
                                     'description':description,
                                     'private':'False'})
        
        
        print response
        
        #test if we have a message that fork is ok
        assert 'fork %s repository as %s task added' \
                      % (repo_name, fork_name) in response.session['flash'][0], 'No flash message about fork'
                      
        #test if the fork was created in the database
        fork_repo = self.sa.query(Repository).filter(Repository.repo_name == fork_name).one()
        
        assert fork_repo.repo_name == fork_name, 'wrong name of repo name in new db fork repo'
        assert fork_repo.fork.repo_name == repo_name, 'wron fork parrent'
        
        
        #test if fork is visible in the list ?
        response.follow()
        
        print response
        assert False
