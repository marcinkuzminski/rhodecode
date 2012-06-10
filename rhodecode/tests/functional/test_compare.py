from rhodecode.tests import *


class TestCompareController(TestController):

    def test_index_tag(self):
        self.log_user()
        tag1='0.1.3'
        tag2='0.1.2'
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
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--1c5cf9e91c12">docs/api/utils/index.rst</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--e3305437df55">test_and_report.sh</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--c8e92ef85cd1">.hgignore</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--6e08b694d687">.hgtags</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--2c14b00f3393">docs/api/index.rst</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--430ccbc82bdf">vcs/__init__.py</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--9c390eb52cd6">vcs/backends/hg.py</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--ebb592c595c0">vcs/utils/__init__.py</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--7abc741b5052">vcs/utils/annotate.py</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--2ef0ef106c56">vcs/utils/diffs.py</a></div>''' % (HG_REPO, tag1,  tag2))
        response.mustcontain('''<div class="node"><a href="/%s/compare/tag@%s...tag@%s#C--3150cb87d4b7">vcs/utils/lazy.py</a></div>''' % (HG_REPO, tag1,  tag2))

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
