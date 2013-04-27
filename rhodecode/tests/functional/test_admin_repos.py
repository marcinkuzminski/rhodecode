# -*- coding: utf-8 -*-

import os
import urllib

from rhodecode.lib import vcs
from rhodecode.model.db import Repository, RepoGroup, UserRepoToPerm, User,\
    Permission
from rhodecode.tests import *
from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.meta import Session
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def _get_permission_for_user(user, repo):
    perm = UserRepoToPerm.query()\
                .filter(UserRepoToPerm.repository ==
                        Repository.get_by_repo_name(repo))\
                .filter(UserRepoToPerm.user == User.get_by_username(user))\
                .all()
    return perm


class TestAdminReposController(TestController):

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
        response = self.app.post(url('repos'),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_name=repo_name,
                                                repo_description=description))
        self.checkSessionFlash(response,
                               'Created repository <a href="/%s">%s</a>'
                               % (repo_name, repo_name))

        #test if the repo was created in the database
        new_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name).one()

        self.assertEqual(new_repo.repo_name, repo_name)
        self.assertEqual(new_repo.description, description)

        #test if repository is visible in the list ?
        response = response.follow()

        response.mustcontain(repo_name)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except Exception:
            self.fail('no repo %s in filesystem' % repo_name)

    def test_create_hg_non_ascii(self):
        self.log_user()
        non_ascii = "ąęł"
        repo_name = "%s%s" % (NEW_HG_REPO, non_ascii)
        repo_name_unicode = repo_name.decode('utf8')
        description = 'description for newly created repo' + non_ascii
        description_unicode = description.decode('utf8')
        private = False
        response = self.app.post(url('repos'),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_name=repo_name,
                                                repo_description=description))
        self.checkSessionFlash(response,
                               u'Created repository <a href="/%s">%s</a>'
                               % (urllib.quote(repo_name), repo_name_unicode))
        #test if the repo was created in the database
        new_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name_unicode).one()

        self.assertEqual(new_repo.repo_name, repo_name_unicode)
        self.assertEqual(new_repo.description, description_unicode)

        #test if repository is visible in the list ?
        response = response.follow()

        response.mustcontain(repo_name)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except Exception:
            self.fail('no repo %s in filesystem' % repo_name)

    def test_create_hg_in_group(self):
        self.log_user()

        ## create GROUP
        group_name = 'sometest'
        gr = ReposGroupModel().create(group_name=group_name,
                                      group_description='test',
                                      owner=TEST_USER_ADMIN_LOGIN)
        Session().commit()

        repo_name = 'ingroup'
        repo_name_full = RepoGroup.url_sep().join([group_name, repo_name])
        description = 'description for newly created repo'
        response = self.app.post(url('repos'),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_name=repo_name,
                                                repo_description=description,
                                                repo_group=gr.group_id,))

        self.checkSessionFlash(response,
                               'Created repository <a href="/%s">%s</a>'
                               % (repo_name_full, repo_name))
        #test if the repo was created in the database
        new_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name_full).one()

        self.assertEqual(new_repo.repo_name, repo_name_full)
        self.assertEqual(new_repo.description, description)

        #test if repository is visible in the list ?
        response = response.follow()

        response.mustcontain(repo_name_full)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name_full))
        except Exception:
            ReposGroupModel().delete(group_name)
            Session().commit()
            self.fail('no repo %s in filesystem' % repo_name)

        RepoModel().delete(repo_name_full)
        ReposGroupModel().delete(group_name)
        Session().commit()

    def test_create_git(self):
        self.log_user()
        repo_name = NEW_GIT_REPO
        description = 'description for newly created repo'

        response = self.app.post(url('repos'),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_type='git',
                                                repo_name=repo_name,
                                                repo_description=description))
        self.checkSessionFlash(response,
                               'Created repository <a href="/%s">%s</a>'
                               % (repo_name, repo_name))

        #test if the repo was created in the database
        new_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name).one()

        self.assertEqual(new_repo.repo_name, repo_name)
        self.assertEqual(new_repo.description, description)

        #test if repository is visible in the list ?
        response = response.follow()

        response.mustcontain(repo_name)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except Exception:
            self.fail('no repo %s in filesystem' % repo_name)

    def test_create_git_non_ascii(self):
        self.log_user()
        non_ascii = "ąęł"
        repo_name = "%s%s" % (NEW_GIT_REPO, non_ascii)
        repo_name_unicode = repo_name.decode('utf8')
        description = 'description for newly created repo' + non_ascii
        description_unicode = description.decode('utf8')
        private = False
        response = self.app.post(url('repos'),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_type='git',
                                                repo_name=repo_name,
                                                repo_description=description))

        self.checkSessionFlash(response,
                               u'Created repository <a href="/%s">%s</a>'
                               % (urllib.quote(repo_name), repo_name_unicode))

        #test if the repo was created in the database
        new_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name_unicode).one()

        self.assertEqual(new_repo.repo_name, repo_name_unicode)
        self.assertEqual(new_repo.description, description_unicode)

        #test if repository is visible in the list ?
        response = response.follow()

        response.mustcontain(repo_name)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except Exception:
            self.fail('no repo %s in filesystem' % repo_name)

    def test_update(self):
        response = self.app.put(url('repo', repo_name=HG_REPO))

    def test_update_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name=HG_REPO),
                                 params=dict(_method='put'))

    def test_delete_hg(self):
        self.log_user()
        repo_name = 'vcs_test_new_to_delete'
        description = 'description for newly created repo'
        response = self.app.post(url('repos'),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_type='hg',
                                                repo_name=repo_name,
                                                repo_description=description))

        self.checkSessionFlash(response,
                               'Created repository <a href="/%s">%s</a>'
                               % (repo_name, repo_name))
        #test if the repo was created in the database
        new_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name).one()

        self.assertEqual(new_repo.repo_name, repo_name)
        self.assertEqual(new_repo.description, description)

        #test if repository is visible in the list ?
        response = response.follow()

        response.mustcontain(repo_name)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except Exception:
            self.fail('no repo %s in filesystem' % repo_name)

        response = self.app.delete(url('repo', repo_name=repo_name))

        self.checkSessionFlash(response, 'Deleted repository %s' % (repo_name))

        response.follow()

        #check if repo was deleted from db
        deleted_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name).scalar()

        self.assertEqual(deleted_repo, None)

        self.assertEqual(os.path.isdir(os.path.join(TESTS_TMP_PATH, repo_name)),
                                  False)

    def test_delete_git(self):
        self.log_user()
        repo_name = 'vcs_test_new_to_delete'
        description = 'description for newly created repo'
        private = False
        response = self.app.post(url('repos'),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_type='git',
                                                repo_name=repo_name,
                                                repo_description=description))

        self.checkSessionFlash(response,
                               'Created repository <a href="/%s">%s</a>'
                               % (repo_name, repo_name))
        #test if the repo was created in the database
        new_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name).one()

        self.assertEqual(new_repo.repo_name, repo_name)
        self.assertEqual(new_repo.description, description)

        #test if repository is visible in the list ?
        response = response.follow()

        response.mustcontain(repo_name)

        #test if repository was created on filesystem
        try:
            vcs.get_repo(os.path.join(TESTS_TMP_PATH, repo_name))
        except Exception:
            self.fail('no repo %s in filesystem' % repo_name)

        response = self.app.delete(url('repo', repo_name=repo_name))

        self.checkSessionFlash(response, 'Deleted repository %s' % (repo_name))

        response.follow()

        #check if repo was deleted from db
        deleted_repo = Session().query(Repository)\
            .filter(Repository.repo_name == repo_name).scalar()

        self.assertEqual(deleted_repo, None)

        self.assertEqual(os.path.isdir(os.path.join(TESTS_TMP_PATH, repo_name)),
                                  False)

    def test_delete_repo_with_group(self):
        #TODO:
        pass

    def test_delete_browser_fakeout(self):
        response = self.app.post(url('repo', repo_name=HG_REPO),
                                 params=dict(_method='delete'))

    def test_show_hg(self):
        self.log_user()
        response = self.app.get(url('repo', repo_name=HG_REPO))

    def test_show_git(self):
        self.log_user()
        response = self.app.get(url('repo', repo_name=GIT_REPO))


    def test_edit(self):
        response = self.app.get(url('edit_repo', repo_name=HG_REPO))

    def test_set_private_flag_sets_default_to_none(self):
        self.log_user()
        #initially repository perm should be read
        perm = _get_permission_for_user(user='default', repo=HG_REPO)
        self.assertTrue(len(perm), 1)
        self.assertEqual(perm[0].permission.permission_name, 'repository.read')
        self.assertEqual(Repository.get_by_repo_name(HG_REPO).private, False)

        response = self.app.put(url('repo', repo_name=HG_REPO),
                        fixture._get_repo_create_params(repo_private=1,
                                                repo_name=HG_REPO,
                                                user=TEST_USER_ADMIN_LOGIN))
        self.checkSessionFlash(response,
                               msg='Repository %s updated successfully' % (HG_REPO))
        self.assertEqual(Repository.get_by_repo_name(HG_REPO).private, True)

        #now the repo default permission should be None
        perm = _get_permission_for_user(user='default', repo=HG_REPO)
        self.assertTrue(len(perm), 1)
        self.assertEqual(perm[0].permission.permission_name, 'repository.none')

        response = self.app.put(url('repo', repo_name=HG_REPO),
                        fixture._get_repo_create_params(repo_private=False,
                                                repo_name=HG_REPO,
                                                user=TEST_USER_ADMIN_LOGIN))
        self.checkSessionFlash(response,
                               msg='Repository %s updated successfully' % (HG_REPO))
        self.assertEqual(Repository.get_by_repo_name(HG_REPO).private, False)

        #we turn off private now the repo default permission should stay None
        perm = _get_permission_for_user(user='default', repo=HG_REPO)
        self.assertTrue(len(perm), 1)
        self.assertEqual(perm[0].permission.permission_name, 'repository.none')

        #update this permission back
        perm[0].permission = Permission.get_by_key('repository.read')
        Session().add(perm[0])
        Session().commit()
