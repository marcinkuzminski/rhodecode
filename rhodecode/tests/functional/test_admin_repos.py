# -*- coding: utf-8 -*-

import os
import vcs

from rhodecode.model.db import Repository
from rhodecode.tests import *

class TestAdminReposController(TestController):


    def __make_repo(self):
        pass


    def test_index(self):
        self.log_user()
        response = self.app.get(url('repos'))
        # Test response...

    def test_index_as_xml(self):
        response = self.app.get(url('formatted_repos', format='xml'))

    def test_create_hg(self):
        self.log_user()
        repo_name = NEW_HG_REPO
        description = 'description for newly created repo'
        private = False
        response = self.app.post(url('repos'), {'repo_name':repo_name,
                                                'repo_type':'hg',
                                                'clone_uri':'',
                                                'repo_group':'',
                                                'description':description,
                                                'private':private})

        self.checkSessionFlash(response, 'created repository %s' % (repo_name))

        #test if the repo was created in the database
        new_repo = self.sa.query(Repository).filter(Repository.repo_name ==
                                                    repo_name).one()

        self.assertEqual(new_repo.repo_name, repo_name)
        self.assertEqual(new_repo.description, description)

        #test if repository is visible in the list ?
        response = response.follow()

        self.assertTrue(repo_name in response.body)


        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except:
            self.fail('no repo in filesystem')


    def test_create_hg_non_ascii(self):
        self.log_user()
        non_ascii = "ąęł"
        repo_name = "%s%s" % (NEW_HG_REPO, non_ascii)
        repo_name_unicode = repo_name.decode('utf8')
        description = 'description for newly created repo' + non_ascii
        description_unicode = description.decode('utf8')
        private = False
        response = self.app.post(url('repos'), {'repo_name':repo_name,
                                                'repo_type':'hg',
                                                'clone_uri':'',
                                                'repo_group':'',
                                                'description':description,
                                                'private':private})
        self.checkSessionFlash(response,
                               'created repository %s' % (repo_name_unicode))

        #test if the repo was created in the database
        new_repo = self.sa.query(Repository).filter(Repository.repo_name ==
                                                repo_name_unicode).one()

        self.assertEqual(new_repo.repo_name, repo_name_unicode)
        self.assertEqual(new_repo.description, description_unicode)

        #test if repository is visible in the list ?
        response = response.follow()

        self.assertTrue(repo_name in response.body)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except:
            self.fail('no repo in filesystem')


    def test_create_hg_in_group(self):
        #TODO: write test !
        pass

    def test_create_git(self):
        return
        self.log_user()
        repo_name = NEW_GIT_REPO
        description = 'description for newly created repo'
        private = False
        response = self.app.post(url('repos'), {'repo_name':repo_name,
                                                'repo_type':'git',
                                                'clone_uri':'',
                                                'repo_group':'',
                                                'description':description,
                                                'private':private})


        #test if we have a message for that repository
        assert '''created repository %s''' % (repo_name) in response.session['flash'][0], 'No flash message about new repo'

        #test if the fork was created in the database
        new_repo = self.sa.query(Repository).filter(Repository.repo_name == repo_name).one()

        assert new_repo.repo_name == repo_name, 'wrong name of repo name in db'
        assert new_repo.description == description, 'wrong description'

        #test if repository is visible in the list ?
        response = response.follow()

        assert repo_name in response.body, 'missing new repo from the main repos list'

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except:
            assert False , 'no repo in filesystem'

    def test_new(self):
        self.log_user()
        response = self.app.get(url('new_repo'))

    def test_new_as_xml(self):
        response = self.app.get(url('formatted_new_repo', format='xml'))

    def test_update(self):
        response = self.app.put(url('repo', repo_name=HG_REPO))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name=HG_REPO),
                                 params=dict(_method='put'))

    def test_delete(self):
        self.log_user()
        repo_name = 'vcs_test_new_to_delete'
        description = 'description for newly created repo'
        private = False

        response = self.app.post(url('repos'), {'repo_name':repo_name,
                                                'repo_type':'hg',
                                                'clone_uri':'',
                                                'repo_group':'',
                                                'description':description,
                                                'private':private})
        self.assertTrue('flash' in response.session)

        #test if we have a message for that repository
        self.assertTrue('''created repository %s''' % (repo_name) in
                        response.session['flash'][0])

        #test if the repo was created in the database
        new_repo = self.sa.query(Repository).filter(Repository.repo_name ==
                                                    repo_name).one()

        self.assertEqual(new_repo.repo_name, repo_name)
        self.assertEqual(new_repo.description, description)

        #test if repository is visible in the list ?
        response = response.follow()

        self.assertTrue(repo_name in response.body)


        response = self.app.delete(url('repo', repo_name=repo_name))

        self.assertTrue('''deleted repository %s''' % (repo_name) in
                        response.session['flash'][0])

        response.follow()

        #check if repo was deleted from db
        deleted_repo = self.sa.query(Repository).filter(Repository.repo_name
                                                        == repo_name).scalar()

        self.assertEqual(deleted_repo, None)


    def test_delete_repo_with_group(self):
        #TODO:
        pass


    def test_delete_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name=HG_REPO),
                                 params=dict(_method='delete'))

    def test_show(self):
        self.log_user()
        response = self.app.get(url('repo', repo_name=HG_REPO))

    def test_show_as_xml(self):
        response = self.app.get(url('formatted_repo', repo_name=HG_REPO,
                                    format='xml'))

    def test_edit(self):
        response = self.app.get(url('edit_repo', repo_name=HG_REPO))

    def test_edit_as_xml(self):
        response = self.app.get(url('formatted_edit_repo', repo_name=HG_REPO,
                                    format='xml'))
