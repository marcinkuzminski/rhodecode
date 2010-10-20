from rhodecode.model.db import Repository
from rhodecode.tests import *

class TestReposController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url('repos'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_repos', format='xml'))

    def test_create(self):
        self.log_user()
        repo_name = 'vcs_test_new'
        description = 'description for newly created repo'
        private = False
        response = self.app.post(url('repos'), {'repo_name':repo_name,
                                               'description':description,
                                               'private':private})

        print response
        
        #test if we have a message for that repository
        print '-' * 100
        print response.session
        assert '''created repository %s''' % (repo_name) in response.session['flash'][0], 'No flash message about new repo'
                      
        #test if the fork was created in the database
        new_repo = self.sa.query(Repository).filter(Repository.repo_name == repo_name).one()
        
        assert new_repo.repo_name == repo_name, 'wrong name of repo name in db'
        assert new_repo.description == description, 'wrong description'
        
        #test if repository is visible in the list ?
        response = response.follow()
        
        assert repo_name in response.body, 'missing new repo from the main repos list'
        
                


    def test_new(self):
        self.log_user()
        response = self.app.get(url('new_repo'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_repo', format='xml'))

    def test_update(self):
        response = self.app.put(url('repo', repo_name='vcs_test'))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name='vcs_test'), params=dict(_method='put'))

    def test_delete(self):
        self.log_user()
        repo_name = 'vcs_test_new_to_delete'
        description = 'description for newly created repo'
        private = False
        response = self.app.post(url('repos'), {'repo_name':repo_name,
                                               'description':description,
                                               'private':private})

        print response
        
        #test if we have a message for that repository
        print '-' * 100
        print response.session
        assert '''created repository %s''' % (repo_name) in response.session['flash'][0], 'No flash message about new repo'
                      
        #test if the repo was created in the database
        new_repo = self.sa.query(Repository).filter(Repository.repo_name == repo_name).one()
        
        assert new_repo.repo_name == repo_name, 'wrong name of repo name in db'
        assert new_repo.description == description, 'wrong description'
        
        #test if repository is visible in the list ?
        response = response.follow()
        
        assert repo_name in response.body, 'missing new repo from the main repos list'
        
                
        response = self.app.delete(url('repo', repo_name=repo_name))
        
        print '-' * 100
        print response.session
        assert '''deleted repository %s''' % (repo_name) in response.session['flash'][0], 'No flash message about delete repo'
                
        response.follow()
        
        #check if repo was deleted from db
        deleted_repo = self.sa.query(Repository).filter(Repository.repo_name == repo_name).scalar()
        
        assert deleted_repo is None, 'Deleted repository was found in db'
        

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name='vcs_test'), params=dict(_method='delete'))

    def test_show(self):
        self.log_user()
        response = self.app.get(url('repo', repo_name='vcs_test'))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_repo', repo_name='vcs_test', format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_repo', repo_name='vcs_test'))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_repo', repo_name='vcs_test', format='xml'))
