from rhodecode.tests import *
from rhodecode.model.db import UserRepoToPerm, Repository, User, Permission
from rhodecode.model.meta import Session


def _get_permission_for_user(user, repo):
    perm = UserRepoToPerm.query()\
                .filter(UserRepoToPerm.repository ==
                        Repository.get_by_repo_name(repo))\
                .filter(UserRepoToPerm.user == User.get_by_username(user))\
                .all()
    return perm


class TestSettingsController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='settings', action='index',
                                    repo_name=HG_REPO))
        # Test response...

    def test_set_private_flag_sets_default_to_none(self):
        self.log_user()
        #initially repository perm should be read
        perm = _get_permission_for_user(user='default', repo=HG_REPO)
        self.assertTrue(len(perm), 1)
        self.assertEqual(perm[0].permission.permission_name, 'repository.read')
        self.assertEqual(Repository.get_by_repo_name(HG_REPO).private, False)

        response = self.app.put(url('repo', repo_name=HG_REPO),
                        _get_repo_create_params(repo_private=1,
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
                        _get_repo_create_params(repo_private=False,
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
        