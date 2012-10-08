from rhodecode.tests import *
from rhodecode.model.repo import RepoModel
from rhodecode.model.meta import Session
from rhodecode.model.db import Repository
from rhodecode.model.scm import ScmModel
from rhodecode.lib.vcs.backends.base import EmptyChangeset


class TestCompareController(TestController):

    def test_index_tag(self):
        self.log_user()
        tag1 = '0.1.3'
        tag2 = '0.1.2'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=HG_REPO,
                                    org_ref_type="tag",
                                    org_ref=tag1,
                                    other_ref_type="tag",
                                    other_ref=tag2,
                                    ))
        response.mustcontain('%s@%s -> %s@%s' % (HG_REPO, tag1, HG_REPO, tag2))
        ## outgoing changesets between tags
        response.mustcontain('''<a href="/%s/changeset/17544fbfcd33ffb439e2b728b5d526b1ef30bfcf">r120:17544fbfcd33</a>''' % HG_REPO)
        response.mustcontain('''<a href="/%s/changeset/36e0fc9d2808c5022a24f49d6658330383ed8666">r119:36e0fc9d2808</a>''' % HG_REPO)
        response.mustcontain('''<a href="/%s/changeset/bb1a3ab98cc45cb934a77dcabf87a5a598b59e97">r118:bb1a3ab98cc4</a>''' % HG_REPO)
        response.mustcontain('''<a href="/%s/changeset/41fda979f02fda216374bf8edac4e83f69e7581c">r117:41fda979f02f</a>''' % HG_REPO)
        response.mustcontain('''<a href="/%s/changeset/9749bfbfc0d2eba208d7947de266303b67c87cda">r116:9749bfbfc0d2</a>''' % HG_REPO)
        response.mustcontain('''<a href="/%s/changeset/70d4cef8a37657ee4cf5aabb3bd9f68879769816">r115:70d4cef8a376</a>''' % HG_REPO)
        response.mustcontain('''<a href="/%s/changeset/c5ddebc06eaaba3010c2d66ea6ec9d074eb0f678">r112:c5ddebc06eaa</a>''' % HG_REPO)

        ## files diff
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--1c5cf9e91c12">docs/api/utils/index.rst</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--e3305437df55">test_and_report.sh</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--c8e92ef85cd1">.hgignore</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--6e08b694d687">.hgtags</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--2c14b00f3393">docs/api/index.rst</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--430ccbc82bdf">vcs/__init__.py</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--9c390eb52cd6">vcs/backends/hg.py</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--ebb592c595c0">vcs/utils/__init__.py</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--7abc741b5052">vcs/utils/annotate.py</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--2ef0ef106c56">vcs/utils/diffs.py</a></div>''' % (HG_REPO, tag1, tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--3150cb87d4b7">vcs/utils/lazy.py</a></div>''' % (HG_REPO, tag1, tag2))

    def test_index_branch(self):
        self.log_user()
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=HG_REPO,
                                    org_ref_type="branch",
                                    org_ref='default',
                                    other_ref_type="branch",
                                    other_ref='default',
                                    ))

        response.mustcontain('%s@default -> %s@default' % (HG_REPO, HG_REPO))
        # branch are equal
        response.mustcontain('<tr><td>No changesets</td></tr>')

    def test_compare_revisions(self):
        self.log_user()
        rev1 = '3d8f361e72ab'
        rev2 = 'b986218ba1c9'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=HG_REPO,
                                    org_ref_type="rev",
                                    org_ref=rev1,
                                    other_ref_type="rev",
                                    other_ref=rev2,
                                    ))
        response.mustcontain('%s@%s -> %s@%s' % (HG_REPO, rev1, HG_REPO, rev2))
        ## outgoing changesets between those revisions
        response.mustcontain("""<a href="/%s/changeset/3d8f361e72ab303da48d799ff1ac40d5ac37c67e">r1:%s</a>""" % (HG_REPO, rev1))

        ## files
        response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--c8e92ef85cd1">.hgignore</a>""" % (HG_REPO, rev1, rev2))

    def test_compare_remote_repos(self):
        self.log_user()

        form_data = dict(
            repo_name=HG_FORK,
            repo_name_full=HG_FORK,
            repo_group=None,
            repo_type='hg',
            description='',
            private=False,
            copy_permissions=False,
            landing_rev='tip',
            update_after_clone=False,
            fork_parent_id=Repository.get_by_repo_name(HG_REPO),
        )
        RepoModel().create_fork(form_data, cur_user=TEST_USER_ADMIN_LOGIN)

        Session().commit()

        rev1 = '7d4bc8ec6be5'
        rev2 = '56349e29c2af'

        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=HG_REPO,
                                    org_ref_type="rev",
                                    org_ref=rev1,
                                    other_ref_type="rev",
                                    other_ref=rev2,
                                    repo=HG_FORK
                                    ))

        try:
            response.mustcontain('%s@%s -> %s@%s' % (HG_REPO, rev1, HG_FORK, rev2))
            ## outgoing changesets between those revisions

            response.mustcontain("""<a href="/%s/changeset/7d4bc8ec6be56c0f10425afb40b6fc315a4c25e7">r6:%s</a>""" % (HG_REPO, rev1))
            response.mustcontain("""<a href="/%s/changeset/6fff84722075f1607a30f436523403845f84cd9e">r5:6fff84722075</a>""" % (HG_REPO))
            response.mustcontain("""<a href="/%s/changeset/2dda4e345facb0ccff1a191052dd1606dba6781d">r4:2dda4e345fac</a>""" % (HG_REPO))

            ## files
            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--9c390eb52cd6">vcs/backends/hg.py</a>""" % (HG_REPO, rev1, rev2))
            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--41b41c1f2796">vcs/backends/__init__.py</a>""" % (HG_REPO, rev1, rev2))
            response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s#C--2f574d260608">vcs/backends/base.py</a>""" % (HG_REPO, rev1, rev2))
        finally:
            RepoModel().delete(HG_FORK)

    def test_compare_extra_commits(self):
        self.log_user()

        repo1 = RepoModel().create_repo(repo_name='one', repo_type='hg',
                                        description='diff-test',
                                        owner=TEST_USER_ADMIN_LOGIN)

        repo2 = RepoModel().create_repo(repo_name='one-fork', repo_type='hg',
                                        description='diff-test',
                                        owner=TEST_USER_ADMIN_LOGIN)

        Session().commit()
        r1_id = repo1.repo_id
        r1_name = repo1.repo_name
        r2_id = repo2.repo_id
        r2_name = repo2.repo_name

        #commit something !
        cs0 = ScmModel().create_node(
            repo=repo1.scm_instance, repo_name=r1_name,
            cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit1',
            content='line1',
            f_path='file1'
        )

        cs0_prim = ScmModel().create_node(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit1',
            content='line1',
            f_path='file1'
        )

        cs1 = ScmModel().commit_change(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=cs0_prim, user=TEST_USER_ADMIN_LOGIN, author=TEST_USER_ADMIN_LOGIN,
            message='commit2',
            content='line1\nline2',
            f_path='file1'
        )

        rev1 = 'default'
        rev2 = 'default'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=r2_name,
                                    org_ref_type="branch",
                                    org_ref=rev1,
                                    other_ref_type="branch",
                                    other_ref=rev2,
                                    repo=r1_name
                                    ))

        try:
            response.mustcontain('%s@%s -> %s@%s' % (r2_name, rev1, r1_name, rev2))

            response.mustcontain("""<div class="message">commit2</div>""")
            response.mustcontain("""<a href="/%s/changeset/%s">r1:%s</a>""" % (r2_name, cs1.raw_id, cs1.short_id))
            ## files
            response.mustcontain("""<a href="/%s/compare/branch@%s...branch@%s#C--826e8142e6ba">file1</a>""" % (r2_name, rev1, rev2))

        finally:
            RepoModel().delete(r1_id)
            RepoModel().delete(r2_id)

    def test_org_repo_new_commits_after_forking(self):
        self.log_user()

        repo1 = RepoModel().create_repo(repo_name='one', repo_type='hg',
                                        description='diff-test',
                                        owner=TEST_USER_ADMIN_LOGIN)

        Session().commit()
        r1_id = repo1.repo_id
        r1_name = repo1.repo_name

        #commit something initially !
        cs0 = ScmModel().create_node(
            repo=repo1.scm_instance, repo_name=r1_name,
            cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit1',
            content='line1',
            f_path='file1'
        )
        Session().commit()
        self.assertEqual(repo1.scm_instance.revisions, [cs0.raw_id])
        #fork the repo1
        repo2 = RepoModel().create_repo(repo_name='one-fork', repo_type='hg',
                                description='compare-test',
                                clone_uri=repo1.repo_full_path,
                                owner=TEST_USER_ADMIN_LOGIN, fork_of='one')
        Session().commit()
        self.assertEqual(repo2.scm_instance.revisions, [cs0.raw_id])
        r2_id = repo2.repo_id
        r2_name = repo2.repo_name

        #make 3 new commits in fork
        cs1 = ScmModel().create_node(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=repo2.scm_instance[-1], user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit1-fork',
            content='file1-line1-from-fork',
            f_path='file1-fork'
        )
        cs2 = ScmModel().create_node(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=cs1, user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit2-fork',
            content='file2-line1-from-fork',
            f_path='file2-fork'
        )
        cs3 = ScmModel().create_node(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=cs2, user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit3-fork',
            content='file3-line1-from-fork',
            f_path='file3-fork'
        )

        #compare !
        rev1 = 'default'
        rev2 = 'default'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=r2_name,
                                    org_ref_type="branch",
                                    org_ref=rev1,
                                    other_ref_type="branch",
                                    other_ref=rev2,
                                    repo=r1_name,
                                    bundle=True,
                                    ))

        try:
            response.mustcontain('%s@%s -> %s@%s' % (r2_name, rev1, r1_name, rev2))
            response.mustcontain("""file1-line1-from-fork""")
            response.mustcontain("""file2-line1-from-fork""")
            response.mustcontain("""file3-line1-from-fork""")

            #add new commit into parent !
            cs0 = ScmModel().create_node(
                repo=repo1.scm_instance, repo_name=r1_name,
                cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
                author=TEST_USER_ADMIN_LOGIN,
                message='commit2',
                content='line1-from-new-parent',
                f_path='file2'
            )
            #compare !
            rev1 = 'default'
            rev2 = 'default'
            response = self.app.get(url(controller='compare', action='index',
                                        repo_name=r2_name,
                                        org_ref_type="branch",
                                        org_ref=rev1,
                                        other_ref_type="branch",
                                        other_ref=rev2,
                                        repo=r1_name,
                                        bundle=True,
                                        ))

            response.mustcontain('%s@%s -> %s@%s' % (r2_name, rev1, r1_name, rev2))
            response.mustcontain("""<a href="#">file2</a>""")  # new commit from parent
            response.mustcontain("""line1-from-new-parent""")
            response.mustcontain("""file1-line1-from-fork""")
            response.mustcontain("""file2-line1-from-fork""")
            response.mustcontain("""file3-line1-from-fork""")
        finally:
            RepoModel().delete(r2_id)
            RepoModel().delete(r1_id)

    def test_org_repo_new_commits_after_forking_simple_diff(self):
        self.log_user()

        repo1 = RepoModel().create_repo(repo_name='one', repo_type='hg',
                                        description='diff-test',
                                        owner=TEST_USER_ADMIN_LOGIN)

        Session().commit()
        r1_id = repo1.repo_id
        r1_name = repo1.repo_name

        #commit something initially !
        cs0 = ScmModel().create_node(
            repo=repo1.scm_instance, repo_name=r1_name,
            cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit1',
            content='line1',
            f_path='file1'
        )
        Session().commit()
        self.assertEqual(repo1.scm_instance.revisions, [cs0.raw_id])
        #fork the repo1
        repo2 = RepoModel().create_repo(repo_name='one-fork', repo_type='hg',
                                description='compare-test',
                                clone_uri=repo1.repo_full_path,
                                owner=TEST_USER_ADMIN_LOGIN, fork_of='one')
        Session().commit()
        self.assertEqual(repo2.scm_instance.revisions, [cs0.raw_id])
        r2_id = repo2.repo_id
        r2_name = repo2.repo_name

        #make 3 new commits in fork
        cs1 = ScmModel().create_node(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=repo2.scm_instance[-1], user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit1-fork',
            content='file1-line1-from-fork',
            f_path='file1-fork'
        )
        cs2 = ScmModel().create_node(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=cs1, user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit2-fork',
            content='file2-line1-from-fork',
            f_path='file2-fork'
        )
        cs3 = ScmModel().create_node(
            repo=repo2.scm_instance, repo_name=r2_name,
            cs=cs2, user=TEST_USER_ADMIN_LOGIN,
            author=TEST_USER_ADMIN_LOGIN,
            message='commit3-fork',
            content='file3-line1-from-fork',
            f_path='file3-fork'
        )

        #compare !
        rev1 = 'default'
        rev2 = 'default'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=r2_name,
                                    org_ref_type="branch",
                                    org_ref=rev1,
                                    other_ref_type="branch",
                                    other_ref=rev2,
                                    repo=r1_name,
                                    bundle=False,
                                    ))

        try:
            #response.mustcontain('%s@%s -> %s@%s' % (r2_name, rev1, r1_name, rev2))

            #add new commit into parent !
            cs0 = ScmModel().create_node(
                repo=repo1.scm_instance, repo_name=r1_name,
                cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
                author=TEST_USER_ADMIN_LOGIN,
                message='commit2',
                content='line1',
                f_path='file2'
            )
            #compare !
            rev1 = 'default'
            rev2 = 'default'
            response = self.app.get(url(controller='compare', action='index',
                                        repo_name=r2_name,
                                        org_ref_type="branch",
                                        org_ref=rev1,
                                        other_ref_type="branch",
                                        other_ref=rev2,
                                        repo=r1_name,
                                        bundle=False
                                        ))
            rev2 = cs0.parents[0].raw_id
            response.mustcontain('%s@%s -> %s@%s' % (r2_name, rev1, r1_name, rev2))
            response.mustcontain("""file1-line1-from-fork""")
            response.mustcontain("""file2-line1-from-fork""")
            response.mustcontain("""file3-line1-from-fork""")
            self.assertFalse("""<a href="#">file2</a>""" in response.body)  # new commit from parent
            self.assertFalse("""line1-from-new-parent"""  in response.body)
        finally:
            RepoModel().delete(r2_id)
            RepoModel().delete(r1_id)
