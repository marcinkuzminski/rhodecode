from rhodecode.tests import *

from rhodecode.model.db import Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel


class TestForksController(TestController):

    def setUp(self):
        self.username = u'forkuser'
        self.password = u'qweqwe'
        self.u1 = UserModel().create_or_update(
            username=self.username, password=self.password,
            email=u'fork_king@rhodecode.org', name=u'u1', lastname=u'u1'
        )
        self.Session.commit()

    def tearDown(self):
        self.Session.delete(self.u1)
        self.Session.commit()

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
        org_repo = Repository.get_by_repo_name(repo_name)
        response = self.app.post(url(controller='forks',
                                     action='fork_create',
                                    repo_name=repo_name),
                                    {'repo_name':fork_name,
                                     'repo_group':'',
                                     'fork_parent_id':org_repo.repo_id,
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

    def test_z_fork_create(self):
        self.log_user()
        fork_name = HG_FORK
        description = 'fork of vcs test'
        repo_name = HG_REPO
        org_repo = Repository.get_by_repo_name(repo_name)
        response = self.app.post(url(controller='forks', action='fork_create',
                                    repo_name=repo_name),
                                    {'repo_name':fork_name,
                                     'repo_group':'',
                                     'fork_parent_id':org_repo.repo_id,
                                     'repo_type':'hg',
                                     'description':description,
                                     'private':'False'})

        #test if we have a message that fork is ok
        self.assertTrue('forked %s repository as %s' \
                      % (repo_name, fork_name) in response.session['flash'][0])

        #test if the fork was created in the database
        fork_repo = self.Session.query(Repository)\
            .filter(Repository.repo_name == fork_name).one()

        self.assertEqual(fork_repo.repo_name, fork_name)
        self.assertEqual(fork_repo.fork.repo_name, repo_name)

        #test if fork is visible in the list ?
        response = response.follow()

        # check if fork is marked as fork
        # wait for cache to expire
        import time
        time.sleep(10)
        response = self.app.get(url(controller='summary', action='index',
                                    repo_name=fork_name))

        self.assertTrue('Fork of %s' % repo_name in response.body)

    def test_zz_fork_permission_page(self):
        usr = self.log_user(self.username, self.password)['user_id']
        repo_name = HG_REPO

        forks = self.Session.query(Repository)\
            .filter(Repository.fork_id != None)\
            .all()
        self.assertEqual(1, len(forks))

        # set read permissions for this
        RepoModel().grant_user_permission(repo=forks[0],
                                          user=usr,
                                          perm='repository.read')
        self.Session.commit()

        response = self.app.get(url(controller='forks', action='forks',
                                    repo_name=repo_name))

        response.mustcontain('<div style="padding:5px 3px 3px 42px;">fork of vcs test</div>')

    def test_zzz_fork_permission_page(self):
        usr = self.log_user(self.username, self.password)['user_id']
        repo_name = HG_REPO

        forks = self.Session.query(Repository)\
            .filter(Repository.fork_id != None)\
            .all()
        self.assertEqual(1, len(forks))

        # set none
        RepoModel().grant_user_permission(repo=forks[0],
                                          user=usr, perm='repository.none')
        self.Session.commit()
        # fork shouldn't be there
        response = self.app.get(url(controller='forks', action='forks',
                                    repo_name=repo_name))
        response.mustcontain('There are no forks yet')
