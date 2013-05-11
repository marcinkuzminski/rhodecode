from rhodecode.tests import *
from rhodecode.model.repo import RepoModel
from rhodecode.model.meta import Session
from rhodecode.model.db import Repository
from rhodecode.model.scm import ScmModel
from rhodecode.lib.vcs.backends.base import EmptyChangeset
from rhodecode.tests.fixture import Fixture

fixture = Fixture()


def _commit_change(repo, filename, content, message, vcs_type, parent=None, newfile=False):
    repo = Repository.get_by_repo_name(repo)
    _cs = parent
    if not parent:
        _cs = EmptyChangeset(alias=vcs_type)

    if newfile:
        nodes = {
            filename: {
                'content': content
            }
        }
        cs = ScmModel().create_nodes(
            user=TEST_USER_ADMIN_LOGIN, repo=repo,
            message=message,
            nodes=nodes,
            parent_cs=_cs,
            author=TEST_USER_ADMIN_LOGIN,
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

    def setUp(self):
        self.r1_id = None
        self.r2_id = None

    def tearDown(self):
        if self.r2_id:
            RepoModel().delete(self.r2_id)
        if self.r1_id:
            RepoModel().delete(self.r1_id)
        Session().commit()
        Session.remove()

    def test_compare_forks_on_branch_extra_commits_hg(self):
        self.log_user()
        repo1 = fixture.create_repo('one', repo_type='hg',
                                    repo_description='diff-test',
                                    cur_user=TEST_USER_ADMIN_LOGIN)
        self.r1_id = repo1.repo_id
        #commit something !
        cs0 = _commit_change(repo1.repo_name, filename='file1', content='line1\n',
                             message='commit1', vcs_type='hg', parent=None, newfile=True)

        #fork this repo
        repo2 = fixture.create_fork('one', 'one-fork')
        self.r2_id = repo2.repo_id

        #add two extra commit into fork
        cs1 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\n',
                             message='commit2', vcs_type='hg', parent=cs0)

        cs2 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\nline3\n',
                             message='commit3', vcs_type='hg', parent=cs1)

        rev1 = 'default'
        rev2 = 'default'

        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=repo1.repo_name,
                                    org_ref_type="branch",
                                    org_ref=rev2,
                                    other_repo=repo2.repo_name,
                                    other_ref_type="branch",
                                    other_ref=rev1,
                                    merge='1',
                                    ))

        response.mustcontain('%s@%s -&gt; %s@%s' % (repo1.repo_name, rev2, repo2.repo_name, rev1))
        response.mustcontain("""Showing 2 commits""")
        response.mustcontain("""1 file changed with 2 insertions and 0 deletions""")

        response.mustcontain("""<div class="message tooltip" title="commit2" style="white-space:normal">commit2</div>""")
        response.mustcontain("""<div class="message tooltip" title="commit3" style="white-space:normal">commit3</div>""")

        response.mustcontain("""<a href="/%s/changeset/%s">r1:%s</a>""" % (repo2.repo_name, cs1.raw_id, cs1.short_id))
        response.mustcontain("""<a href="/%s/changeset/%s">r2:%s</a>""" % (repo2.repo_name, cs2.raw_id, cs2.short_id))
        ## files
        response.mustcontain("""<a href="/%s/compare/branch@%s...branch@%s?other_repo=%s&amp;merge=1#C--826e8142e6ba">file1</a>""" % (repo1.repo_name, rev2, rev1, repo2.repo_name))
        #swap
        response.mustcontain("""<a href="/%s/compare/branch@%s...branch@%s?other_repo=%s&amp;merge=True">[swap]</a>""" % (repo2.repo_name, rev1, rev2, repo1.repo_name))

    def test_compare_forks_on_branch_extra_commits_origin_has_incomming_hg(self):
        self.log_user()

        repo1 = fixture.create_repo('one', repo_type='hg',
                                    repo_description='diff-test',
                                    cur_user=TEST_USER_ADMIN_LOGIN)

        self.r1_id = repo1.repo_id

        #commit something !
        cs0 = _commit_change(repo1.repo_name, filename='file1', content='line1\n',
                             message='commit1', vcs_type='hg', parent=None, newfile=True)

        #fork this repo
        repo2 = fixture.create_fork('one', 'one-fork')
        self.r2_id = repo2.repo_id

        #now commit something to origin repo
        cs1_prim = _commit_change(repo1.repo_name, filename='file2', content='line1file2\n',
                                  message='commit2', vcs_type='hg', parent=cs0, newfile=True)

        #add two extra commit into fork
        cs1 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\n',
                             message='commit2', vcs_type='hg', parent=cs0)

        cs2 = _commit_change(repo2.repo_name, filename='file1', content='line1\nline2\nline3\n',
                             message='commit3', vcs_type='hg', parent=cs1)

        rev1 = 'default'
        rev2 = 'default'

        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=repo1.repo_name,
                                    org_ref_type="branch",
                                    org_ref=rev2,
                                    other_repo=repo2.repo_name,
                                    other_ref_type="branch",
                                    other_ref=rev1,
                                    merge='x',
                                    ))
        response.mustcontain('%s@%s -&gt; %s@%s' % (repo1.repo_name, rev2, repo2.repo_name, rev1))
        response.mustcontain("""Showing 2 commits""")
        response.mustcontain("""1 file changed with 2 insertions and 0 deletions""")

        response.mustcontain("""<div class="message tooltip" title="commit2" style="white-space:normal">commit2</div>""")
        response.mustcontain("""<div class="message tooltip" title="commit3" style="white-space:normal">commit3</div>""")

        response.mustcontain("""<a href="/%s/changeset/%s">r1:%s</a>""" % (repo2.repo_name, cs1.raw_id, cs1.short_id))
        response.mustcontain("""<a href="/%s/changeset/%s">r2:%s</a>""" % (repo2.repo_name, cs2.raw_id, cs2.short_id))
        ## files
        response.mustcontain("""<a href="/%s/compare/branch@%s...branch@%s?other_repo=%s&amp;merge=x#C--826e8142e6ba">file1</a>""" % (repo1.repo_name, rev2, rev1, repo2.repo_name))
        #swap
        response.mustcontain("""<a href="/%s/compare/branch@%s...branch@%s?other_repo=%s&amp;merge=True">[swap]</a>""" % (repo2.repo_name, rev1, rev2, repo1.repo_name))

    def test_compare_cherry_pick_changesets_from_bottom(self):

#        repo1:
#            cs0:
#            cs1:
#        repo1-fork- in which we will cherry pick bottom changesets
#            cs0:
#            cs1:
#            cs2: x
#            cs3: x
#            cs4: x
#            cs5:
        #make repo1, and cs1+cs2
        self.log_user()

        repo1 = fixture.create_repo('repo1', repo_type='hg',
                                    repo_description='diff-test',
                                    cur_user=TEST_USER_ADMIN_LOGIN)
        self.r1_id = repo1.repo_id

        #commit something !
        cs0 = _commit_change(repo1.repo_name, filename='file1', content='line1\n',
                             message='commit1', vcs_type='hg', parent=None,
                             newfile=True)
        cs1 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\n',
                             message='commit2', vcs_type='hg', parent=cs0)
        #fork this repo
        repo2 = fixture.create_fork('repo1', 'repo1-fork')
        self.r2_id = repo2.repo_id
        #now make cs3-6
        cs2 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\n',
                             message='commit3', vcs_type='hg', parent=cs1)
        cs3 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\nline4\n',
                             message='commit4', vcs_type='hg', parent=cs2)
        cs4 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\nline4\nline5\n',
                             message='commit5', vcs_type='hg', parent=cs3)
        cs5 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\nline4\nline5\nline6\n',
                             message='commit6', vcs_type='hg', parent=cs4)

        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=repo2.repo_name,
                                    org_ref_type="rev",
                                    org_ref=cs1.short_id,  # parent of cs2, in repo2
                                    other_repo=repo1.repo_name,
                                    other_ref_type="rev",
                                    other_ref=cs4.short_id,
                                    merge='True',
                                    ))
        response.mustcontain('%s@%s -&gt; %s@%s' % (repo2.repo_name, cs1.short_id, repo1.repo_name, cs4.short_id))
        response.mustcontain("""Showing 3 commits""")
        response.mustcontain("""1 file changed with 3 insertions and 0 deletions""")

        response.mustcontain("""<div class="message tooltip" title="commit3" style="white-space:normal">commit3</div>""")
        response.mustcontain("""<div class="message tooltip" title="commit4" style="white-space:normal">commit4</div>""")
        response.mustcontain("""<div class="message tooltip" title="commit5" style="white-space:normal">commit5</div>""")

        response.mustcontain("""<a href="/%s/changeset/%s">r2:%s</a>""" % (repo1.repo_name, cs2.raw_id, cs2.short_id))
        response.mustcontain("""<a href="/%s/changeset/%s">r3:%s</a>""" % (repo1.repo_name, cs3.raw_id, cs3.short_id))
        response.mustcontain("""<a href="/%s/changeset/%s">r4:%s</a>""" % (repo1.repo_name, cs4.raw_id, cs4.short_id))
        ## files
        response.mustcontain("""#C--826e8142e6ba">file1</a>""")

    def test_compare_cherry_pick_changesets_from_top(self):
#        repo1:
#            cs0:
#            cs1:
#        repo1-fork- in which we will cherry pick bottom changesets
#            cs0:
#            cs1:
#            cs2:
#            cs3: x
#            cs4: x
#            cs5: x
#
        #make repo1, and cs1+cs2
        self.log_user()
        repo1 = fixture.create_repo('repo1', repo_type='hg',
                                    repo_description='diff-test',
                                    cur_user=TEST_USER_ADMIN_LOGIN)
        self.r1_id = repo1.repo_id

        #commit something !
        cs0 = _commit_change(repo1.repo_name, filename='file1', content='line1\n',
                             message='commit1', vcs_type='hg', parent=None,
                             newfile=True)
        cs1 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\n',
                             message='commit2', vcs_type='hg', parent=cs0)
        #fork this repo
        repo2 = fixture.create_fork('repo1', 'repo1-fork')
        self.r2_id = repo2.repo_id
        #now make cs3-6
        cs2 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\n',
                             message='commit3', vcs_type='hg', parent=cs1)
        cs3 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\nline4\n',
                             message='commit4', vcs_type='hg', parent=cs2)
        cs4 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\nline4\nline5\n',
                             message='commit5', vcs_type='hg', parent=cs3)
        cs5 = _commit_change(repo1.repo_name, filename='file1', content='line1\nline2\nline3\nline4\nline5\nline6\n',
                             message='commit6', vcs_type='hg', parent=cs4)
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=repo1.repo_name,
                                    org_ref_type="rev",
                                    org_ref=cs2.short_id, # parent of cs3, not in repo2
                                    other_ref_type="rev",
                                    other_ref=cs5.short_id,
                                    merge='1',
                                    ))

        response.mustcontain('%s@%s -&gt; %s@%s' % (repo1.repo_name, cs2.short_id, repo1.repo_name, cs5.short_id))
        response.mustcontain("""Showing 3 commits""")
        response.mustcontain("""1 file changed with 3 insertions and 0 deletions""")

        response.mustcontain("""<div class="message tooltip" title="commit4" style="white-space:normal">commit4</div>""")
        response.mustcontain("""<div class="message tooltip" title="commit5" style="white-space:normal">commit5</div>""")
        response.mustcontain("""<div class="message tooltip" title="commit6" style="white-space:normal">commit6</div>""")

        response.mustcontain("""<a href="/%s/changeset/%s">r3:%s</a>""" % (repo1.repo_name, cs3.raw_id, cs3.short_id))
        response.mustcontain("""<a href="/%s/changeset/%s">r4:%s</a>""" % (repo1.repo_name, cs4.raw_id, cs4.short_id))
        response.mustcontain("""<a href="/%s/changeset/%s">r5:%s</a>""" % (repo1.repo_name, cs5.raw_id, cs5.short_id))
        ## files
        response.mustcontain("""#C--826e8142e6ba">file1</a>""")

    def test_compare_cherry_pick_changeset_mixed_branches(self):
        pass
        #TODO write this tastecase

    def test_compare_remote_branches_hg(self):
        self.log_user()

        repo2 = fixture.create_fork(HG_REPO, HG_FORK)
        self.r2_id = repo2.repo_id
        rev1 = '56349e29c2af'
        rev2 = '7d4bc8ec6be5'

        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=HG_REPO,
                                    org_ref_type="rev",
                                    org_ref=rev1,
                                    other_ref_type="rev",
                                    other_ref=rev2,
                                    other_repo=HG_FORK,
                                    merge='1',
                                    ))
        response.mustcontain('%s@%s -&gt; %s@%s' % (HG_REPO, rev1, HG_FORK, rev2))
        ## outgoing changesets between those revisions

        response.mustcontain("""<a href="/%s/changeset/2dda4e345facb0ccff1a191052dd1606dba6781d">r4:2dda4e345fac</a>""" % (HG_FORK))
        response.mustcontain("""<a href="/%s/changeset/6fff84722075f1607a30f436523403845f84cd9e">r5:6fff84722075</a>""" % (HG_FORK))
        response.mustcontain("""<a href="/%s/changeset/7d4bc8ec6be56c0f10425afb40b6fc315a4c25e7">r6:%s</a>""" % (HG_FORK, rev2))

        ## files
        response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s?other_repo=%s&amp;merge=1#C--9c390eb52cd6">vcs/backends/hg.py</a>""" % (HG_REPO, rev1, rev2, HG_FORK))
        response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s?other_repo=%s&amp;merge=1#C--41b41c1f2796">vcs/backends/__init__.py</a>""" % (HG_REPO, rev1, rev2, HG_FORK))
        response.mustcontain("""<a href="/%s/compare/rev@%s...rev@%s?other_repo=%s&amp;merge=1#C--2f574d260608">vcs/backends/base.py</a>""" % (HG_REPO, rev1, rev2, HG_FORK))

    def test_org_repo_new_commits_after_forking_simple_diff(self):
        self.log_user()

        repo1 = fixture.create_repo('one', repo_type='hg',
                                    repo_description='diff-test',
                                    cur_user=TEST_USER_ADMIN_LOGIN)

        self.r1_id = repo1.repo_id
        r1_name = repo1.repo_name

        cs0 = _commit_change(repo=r1_name, filename='file1',
                       content='line1', message='commit1', vcs_type='hg',
                       newfile=True)
        Session().commit()
        self.assertEqual(repo1.scm_instance.revisions, [cs0.raw_id])
        #fork the repo1
        repo2 = fixture.create_repo('one-fork', repo_type='hg',
                                    repo_description='diff-test',
                                    cur_user=TEST_USER_ADMIN_LOGIN,
                                    clone_uri=repo1.repo_full_path,
                                    fork_of='one')
        Session().commit()
        self.assertEqual(repo2.scm_instance.revisions, [cs0.raw_id])
        self.r2_id = repo2.repo_id
        r2_name = repo2.repo_name


        cs1 = _commit_change(repo=r2_name, filename='file1-fork',
                       content='file1-line1-from-fork', message='commit1-fork',
                       vcs_type='hg', parent=repo2.scm_instance[-1],
                       newfile=True)

        cs2 = _commit_change(repo=r2_name, filename='file2-fork',
                       content='file2-line1-from-fork', message='commit2-fork',
                       vcs_type='hg', parent=cs1,
                       newfile=True)

        cs3 = _commit_change(repo=r2_name, filename='file3-fork',
                       content='file3-line1-from-fork', message='commit3-fork',
                       vcs_type='hg', parent=cs2, newfile=True)
        #compare !
        rev1 = 'default'
        rev2 = 'default'

        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=r2_name,
                                    org_ref_type="branch",
                                    org_ref=rev1,
                                    other_ref_type="branch",
                                    other_ref=rev2,
                                    other_repo=r1_name,
                                    merge='1',
                                    ))
        response.mustcontain('%s@%s -&gt; %s@%s' % (r2_name, rev1, r1_name, rev2))
        response.mustcontain('No files')
        response.mustcontain('No changesets')

        #add new commit into parent !
#         cs0 = ScmModel().create_node(
#             repo=repo1.scm_instance, repo_name=r1_name,
#             cs=EmptyChangeset(alias='hg'), user=TEST_USER_ADMIN_LOGIN,
#             author=TEST_USER_ADMIN_LOGIN,
#             message='commit2-parent',
#             content='line1-added-after-fork',
#             f_path='file2'
#         )
        cs0 = _commit_change(repo=r1_name, filename='file2',
                    content='line1-added-after-fork', message='commit2-parent',
                    vcs_type='hg', parent=None, newfile=True)

        #compare !
        rev1 = 'default'
        rev2 = 'default'
        response = self.app.get(url(controller='compare', action='index',
                                    repo_name=r2_name,
                                    org_ref_type="branch",
                                    org_ref=rev1,
                                    other_ref_type="branch",
                                    other_ref=rev2,
                                    other_repo=r1_name,
                                    merge='1',
                                    ))

        response.mustcontain('%s@%s -&gt; %s@%s' % (r2_name, rev1, r1_name, rev2))

        response.mustcontain("""commit2-parent""")
        response.mustcontain("""1 file changed with 1 insertions and 0 deletions""")
        response.mustcontain("""line1-added-after-fork""")
