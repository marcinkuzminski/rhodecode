from rhodecode.tests import *
from rhodecode.model.repo import RepoModel
from rhodecode.model.meta import Session
from rhodecode.model.db import Repository
from rhodecode.model.scm import ScmModel
from rhodecode.lib.vcs.backends.base import EmptyChangeset


def _fork_repo(fork_name, vcs_type, parent=None):
    if vcs_type =='hg':
        _REPO = HG_REPO
    elif vcs_type == 'git':
        _REPO = GIT_REPO

    if parent:
        _REPO = parent

    form_data = dict(
        repo_name=fork_name,
        repo_name_full=fork_name,
        repo_group=None,
        repo_type=vcs_type,
        description='',
        private=False,
        copy_permissions=False,
        landing_rev='tip',
        update_after_clone=False,
        fork_parent_id=Repository.get_by_repo_name(_REPO),
    )
    repo = RepoModel().create_fork(form_data, cur_user=TEST_USER_ADMIN_LOGIN)

    Session().commit()
    return Repository.get_by_repo_name(fork_name)


def _commit_change(repo, filename, content, message, vcs_type, parent=None, newfile=False):
    repo = Repository.get_by_repo_name(repo)
    _cs = parent
    if not parent:
        _cs = EmptyChangeset(alias=vcs_type)

    if newfile:
        cs = ScmModel().create_node(
            repo=repo.scm_instance, repo_name=repo.repo_name,
            cs=_cs, user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message=message,
            content=content,
            f_path=filename
        )
    else:
        cs = ScmModel().commit_change(
            repo=repo.scm_instance, repo_name=repo.repo_name,
            cs=parent, user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message=message,
            content=content,
            f_path=filename
        )
    return cs


class TestCompareController(TestController):

    def test_compare_forks_on_branch_extra_commits_hg(self):
        self.log_user()

        repo1 = RepoModel().create_repo(repo_name='one', repo_type='hg',
                                        description='diff-test',
                                        owner=TEST_USER_ADMIN_LOGIN)
        r1_id = repo1.repo_id
        Session().commit()
        #commit something !
        cs0 = _commit_change(repo1.repo_name, filename='file1', content='line1\n',
                             message='commit1', vcs_type='hg', parent=None, newfile=True)

        #fork this repo
        repo2 = _fork_repo('one-fork', 'hg', parent='one')
        Session().commit()
        r2_id = repo2.repo_id

        #add two extra commit into fork
        cs1 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\n',
                             message='commit2', vcs_type='hg', parent=cs0)

        cs2 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\nline3\n',
                             message='commit3', vcs_type='hg', parent=cs1)

        rev1 = 'default'
        rev2 = 'default'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=repo2.repo_name,
                                    org_ref_type="branch",
                                    org_ref=rev1,
                                    other_ref_type="branch",
                                    other_ref=rev2,
                                    repo=repo1.repo_name
                                    ))

        try:
            response.mustcontain('%s@%s -&gt; %s@%s' % (repo2.repo_name, rev1, repo1.repo_name, rev2))
            response.mustcontain("""Showing 2 commits""")
            response.mustcontain("""1 file changed with 2 insertions and 0 deletions""")

            response.mustcontain("""<div class="message tooltip" title="commit2" style="white-space:normal">commit2</div>""")
            response.mustcontain("""<div class="message tooltip" title="commit3" style="white-space:normal">commit3</div>""")

            response.mustcontain("""<a href="/%s/changeset/%s">r1:%s</a>""" % (repo2.repo_name, cs1.raw_id, cs1.short_id))
            response.mustcontain("""<a href="/%s/changeset/%s">r2:%s</a>""" % (repo2.repo_name, cs2.raw_id, cs2.short_id))
            ## files
            response.mustcontain("""<a href="/%s/compare/branch@%s...branch@%s#C--826e8142e6ba">file1</a>""" % (repo2.repo_name, rev1, rev2))

        finally:
            RepoModel().delete(r2_id)
            RepoModel().delete(r1_id)


    def test_compare_forks_on_branch_extra_commits_origin_has_incomming_hg(self):
        self.log_user()

        repo1 = RepoModel().create_repo(repo_name='one', repo_type='hg',
                                        description='diff-test',
                                        owner=TEST_USER_ADMIN_LOGIN)
        r1_id = repo1.repo_id
        Session().commit()
        #commit something !
        cs0 = _commit_change(repo1.repo_name, filename='file1', content='line1\n',
                             message='commit1', vcs_type='hg', parent=None, newfile=True)

        #fork this repo
        repo2 = _fork_repo('one-fork', 'hg', parent='one')
        Session().commit()

        #now commit something to origin repo
        cs1_prim = _commit_change(repo1.repo_name, filename='file2', content='line1file2\n',
                                  message='commit2', vcs_type='hg', parent=cs0, newfile=True)

        r2_id = repo2.repo_id

        #add two extra commit into fork
        cs1 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\n',
                             message='commit2', vcs_type='hg', parent=cs0)

        cs2 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\nline3\n',
                             message='commit3', vcs_type='hg', parent=cs1)

        rev1 = 'default'
        rev2 = 'default'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=repo2.repo_name,
                                    org_ref_type="branch",
                                    org_ref=rev1,
                                    other_ref_type="branch",
                                    other_ref=rev2,
                                    repo=repo1.repo_name
                                    ))

        try:
            response.mustcontain('%s@%s -&gt; %s@%s' % (repo2.repo_name, rev1, repo1.repo_name, rev2))
            response.mustcontain("""Showing 2 commits""")
            response.mustcontain("""1 file changed with 2 insertions and 0 deletions""")

            response.mustcontain("""<div class="message tooltip" title="commit2" style="white-space:normal">commit2</div>""")
            response.mustcontain("""<div class="message tooltip" title="commit3" style="white-space:normal">commit3</div>""")

            response.mustcontain("""<a href="/%s/changeset/%s">r1:%s</a>""" % (repo2.repo_name, cs1.raw_id, cs1.short_id))
            response.mustcontain("""<a href="/%s/changeset/%s">r2:%s</a>""" % (repo2.repo_name, cs2.raw_id, cs2.short_id))
            ## files
            response.mustcontain("""<a href="/%s/compare/branch@%s...branch@%s#C--826e8142e6ba">file1</a>""" % (repo2.repo_name, rev1, rev2))

        finally:
            RepoModel().delete(r2_id)
            RepoModel().delete(r1_id)


#    def test_compare_remote_repos_remote_flag_off(self):
#        self.log_user()
#        _fork_repo(HG_FORK, 'hg')
#
#        rev1 = '56349e29c2af'
#        rev2 = '7d4bc8ec6be5'
#
#        response = self.app.get(url(controller='compare', action='index',
#                                    repo_name=HG_REPO,
#                                    org_ref_type="rev",
#                                    org_ref=rev1,
#                                    other_ref_type="rev",
#                                    other_ref=rev2,
#                                    repo=HG_FORK,
#                                    bundle=False,
#                                    ))
#
#        try:
#            response.mustcontain('%s@%s -&gt; %s@%s' % (HG_REPO, rev1, HG_FORK, rev2))
#            ## outgoing changesets between those revisions
#
#            response.mustcontain("""<a href="/%s/changeset/2dda4e345facb0ccff1a191052dd1606dba6781d">r4:2dda4e345fac</a>""" % (HG_REPO))
#            response.mustcontain("""<a href="/%s/changeset/6fff84722075f1607a30f436523403845f84cd9e">r5:6fff84722075</a>""" % (HG_REPO))
#            response.mustcontain("""<a href="/%s/changeset/7d4bc8ec6be56c0f10425afb40b6fc315a4c25e7">r6:%s</a>""" % (HG_REPO, rev2))
#
#            ## files
#            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--9c390eb52cd6">vcs/backends/hg.py</a>""" % (HG_REPO, rev1, rev2))
#            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--41b41c1f2796">vcs/backends/__init__.py</a>""" % (HG_REPO, rev1, rev2))
#            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--2f574d260608">vcs/backends/base.py</a>""" % (HG_REPO, rev1, rev2))
#        finally:
#            RepoModel().delete(HG_FORK)



#
#    def test_compare_remote_branches_hg(self):
#        self.log_user()
#
#        _fork_repo(HG_FORK, 'hg')
#
#        rev1 = '56349e29c2af'
#        rev2 = '7d4bc8ec6be5'
#
#        response = self.app.get(url(controller='compare', action='index',
#                                    repo_name=HG_REPO,
#                                    org_ref_type="rev",
#                                    org_ref=rev1,
#                                    other_ref_type="rev",
#                                    other_ref=rev2,
#                                    repo=HG_FORK,
#                                    ))
#
#        try:
#            response.mustcontain('%s@%s -&gt; %s@%s' % (HG_REPO, rev1, HG_FORK, rev2))
#            ## outgoing changesets between those revisions
#
#            response.mustcontain("""<a href="/%s/changeset/2dda4e345facb0ccff1a191052dd1606dba6781d">r4:2dda4e345fac</a>""" % (HG_REPO))
#            response.mustcontain("""<a href="/%s/changeset/6fff84722075f1607a30f436523403845f84cd9e">r5:6fff84722075</a>""" % (HG_REPO))
#            response.mustcontain("""<a href="/%s/changeset/7d4bc8ec6be56c0f10425afb40b6fc315a4c25e7">r6:%s</a>""" % (HG_REPO, rev2))
#
#            ## files
#            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--9c390eb52cd6">vcs/backends/hg.py</a>""" % (HG_REPO, rev1, rev2))
#            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--41b41c1f2796">vcs/backends/__init__.py</a>""" % (HG_REPO, rev1, rev2))
#            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--2f574d260608">vcs/backends/base.py</a>""" % (HG_REPO, rev1, rev2))
#        finally:
#            RepoModel().delete(HG_FORK)
#
#    def test_org_repo_new_commits_after_forking_simple_diff(self):
#        self.log_user()
#
#        repo1 = RepoModel().create_repo(repo_name='one', repo_type='hg',
#                                        description='diff-test',
#                                        owner=TEST_USER_ADMIN_LOGIN)
#
#        Session().commit()
#        r1_id = repo1.repo_id
#        r1_name = repo1.repo_name
#
#        #commit something initially !
#        cs0 = ScmModel().create_node(
#            repo=repo1.scm_instance, repo_name=r1_name,
#            cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
#            author=TEST_USER_ADMIN_LOGIN,
#            message='commit1',
#            content='line1',
#            f_path='file1'
#        )
#        Session().commit()
#        self.assertEqual(repo1.scm_instance.revisions, [cs0.raw_id])
#        #fork the repo1
#        repo2 = RepoModel().create_repo(repo_name='one-fork', repo_type='hg',
#                                description='compare-test',
#                                clone_uri=repo1.repo_full_path,
#                                owner=TEST_USER_ADMIN_LOGIN, fork_of='one')
#        Session().commit()
#        self.assertEqual(repo2.scm_instance.revisions, [cs0.raw_id])
#        r2_id = repo2.repo_id
#        r2_name = repo2.repo_name
#
#        #make 3 new commits in fork
#        cs1 = ScmModel().create_node(
#            repo=repo2.scm_instance, repo_name=r2_name,
#            cs=repo2.scm_instance[-1], user=TEST_USER_ADMIN_LOGIN,
#            author=TEST_USER_ADMIN_LOGIN,
#            message='commit1-fork',
#            content='file1-line1-from-fork',
#            f_path='file1-fork'
#        )
#        cs2 = ScmModel().create_node(
#            repo=repo2.scm_instance, repo_name=r2_name,
#            cs=cs1, user=TEST_USER_ADMIN_LOGIN,
#            author=TEST_USER_ADMIN_LOGIN,
#            message='commit2-fork',
#            content='file2-line1-from-fork',
#            f_path='file2-fork'
#        )
#        cs3 = ScmModel().create_node(
#            repo=repo2.scm_instance, repo_name=r2_name,
#            cs=cs2, user=TEST_USER_ADMIN_LOGIN,
#            author=TEST_USER_ADMIN_LOGIN,
#            message='commit3-fork',
#            content='file3-line1-from-fork',
#            f_path='file3-fork'
#        )
#
#        #compare !
#        rev1 = 'default'
#        rev2 = 'default'
#        response = self.app.get(url(controller='compare', action='index',
#                                    repo_name=r2_name,
#                                    org_ref_type="branch",
#                                    org_ref=rev1,
#                                    other_ref_type="branch",
#                                    other_ref=rev2,
#                                    repo=r1_name,
#                                    bundle=False,
#                                    ))
#
#        try:
#            #response.mustcontain('%s@%s -&gt; %s@%s' % (r2_name, rev1, r1_name, rev2))
#
#            #add new commit into parent !
#            cs0 = ScmModel().create_node(
#                repo=repo1.scm_instance, repo_name=r1_name,
#                cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
#                author=TEST_USER_ADMIN_LOGIN,
#                message='commit2',
#                content='line1',
#                f_path='file2'
#            )
#            #compare !
#            rev1 = 'default'
#            rev2 = 'default'
#            response = self.app.get(url(controller='compare', action='index',
#                                        repo_name=r2_name,
#                                        org_ref_type="branch",
#                                        org_ref=rev1,
#                                        other_ref_type="branch",
#                                        other_ref=rev2,
#                                        repo=r1_name,
#                                        bundle=False
#                                        ))
#
#            response.mustcontain('%s@%s -&gt; %s@%s' % (r2_name, rev1, r1_name, rev2))
#            response.mustcontain("""file1-line1-from-fork""")
#            response.mustcontain("""file2-line1-from-fork""")
#            response.mustcontain("""file3-line1-from-fork""")
#            self.assertFalse("""<a href="#">file2</a>""" in response.body)  # new commit from parent
#            self.assertFalse("""line1-from-new-parent"""  in response.body)
#        finally:
#            RepoModel().delete(r2_id)
#            RepoModel().delete(r1_id)
