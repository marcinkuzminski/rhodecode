from rhodecode.tests import *

from rhodecode.model.meta import Session
from rhodecode.tests.fixture import Fixture
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import Repository
from rhodecode.lib.exceptions import AttachedForksError

fixture = Fixture()


class TestRepos(BaseTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        Session.remove()

    def test_remove_repo(self):
        repo = fixture.create_repo(name='test-repo-1')
        Session().commit()

        RepoModel().delete(repo=repo)
        Session().commit()

        self.assertEqual(None, Repository.get_by_repo_name(repo_name='test-repo-1'))

    def test_remove_repo_repo_raises_exc_when_attached_forks(self):
        repo = fixture.create_repo(name='test-repo-1')
        Session().commit()

        fixture.create_fork(repo.repo_name, 'test-repo-fork-1')
        Session().commit()

        self.assertRaises(AttachedForksError, lambda: RepoModel().delete(repo=repo))

    def test_remove_repo_delete_forks(self):
        repo = fixture.create_repo(name='test-repo-1')
        Session().commit()

        fork = fixture.create_fork(repo.repo_name, 'test-repo-fork-1')
        Session().commit()

        #fork of fork
        fixture.create_fork(fork.repo_name, 'test-repo-fork-fork-1')
        Session().commit()

        RepoModel().delete(repo=repo, forks='delete')
        Session().commit()

        self.assertEqual(None, Repository.get_by_repo_name(repo_name='test-repo-1'))
        self.assertEqual(None, Repository.get_by_repo_name(repo_name='test-repo-fork-1'))
        self.assertEqual(None, Repository.get_by_repo_name(repo_name='test-repo-fork-fork-1'))

    def test_remove_repo_detach_forks(self):
        repo = fixture.create_repo(name='test-repo-1')
        Session().commit()

        fork = fixture.create_fork(repo.repo_name, 'test-repo-fork-1')
        Session().commit()

        #fork of fork
        fixture.create_fork(fork.repo_name, 'test-repo-fork-fork-1')
        Session().commit()

        RepoModel().delete(repo=repo, forks='detach')
        Session().commit()

        try:
            self.assertEqual(None, Repository.get_by_repo_name(repo_name='test-repo-1'))
            self.assertNotEqual(None, Repository.get_by_repo_name(repo_name='test-repo-fork-1'))
            self.assertNotEqual(None, Repository.get_by_repo_name(repo_name='test-repo-fork-fork-1'))
        finally:
            RepoModel().delete(repo='test-repo-fork-fork-1')
            RepoModel().delete(repo='test-repo-fork-1')
            Session().commit()
