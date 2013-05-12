import os
from rhodecode.tests import *
from rhodecode.model.db import Repository
from rhodecode.model.meta import Session
from rhodecode.tests.fixture import Fixture

fixture = Fixture()

ARCHIVE_SPECS = {
    '.tar.bz2': ('application/x-bzip2', 'tbz2', ''),
    '.tar.gz': ('application/x-gzip', 'tgz', ''),
    '.zip': ('application/zip', 'zip', ''),
}


def _set_downloads(repo_name, set_to):
    repo = Repository.get_by_repo_name(repo_name)
    repo.enable_downloads = set_to
    Session().add(repo)
    Session().commit()


class TestFilesController(TestController):

    def test_index(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='index',
                                    repo_name=HG_REPO,
                                    revision='tip',
                                    f_path='/'))
        # Test response...
        response.mustcontain('<a class="browser-dir ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/docs">docs</a>')
        response.mustcontain('<a class="browser-dir ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/vcs">vcs</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/.gitignore">.gitignore</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/.hgignore">.hgignore</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/.hgtags">.hgtags</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/.travis.yml">.travis.yml</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/MANIFEST.in">MANIFEST.in</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/README.rst">README.rst</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/run_test_and_report.sh">run_test_and_report.sh</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/setup.cfg">setup.cfg</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/setup.py">setup.py</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/test_and_report.sh">test_and_report.sh</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/tox.ini">tox.ini</a>')

    def test_index_revision(self):
        self.log_user()

        response = self.app.get(
            url(controller='files', action='index',
                repo_name=HG_REPO,
                revision='7ba66bec8d6dbba14a2155be32408c435c5f4492',
                f_path='/')
        )

        #Test response...

        response.mustcontain('<a class="browser-dir ypjax-link" href="/vcs_test_hg/files/7ba66bec8d6dbba14a2155be32408c435c5f4492/docs">docs</a>')
        response.mustcontain('<a class="browser-dir ypjax-link" href="/vcs_test_hg/files/7ba66bec8d6dbba14a2155be32408c435c5f4492/tests">tests</a>')
        response.mustcontain('<a class="browser-file ypjax-link" href="/vcs_test_hg/files/7ba66bec8d6dbba14a2155be32408c435c5f4492/README.rst">README.rst</a>')
        response.mustcontain('1.1 KiB')
        response.mustcontain('text/x-python')

    def test_index_different_branch(self):
        self.log_user()

        response = self.app.get(url(controller='files', action='index',
                                    repo_name=HG_REPO,
                                    revision='97e8b885c04894463c51898e14387d80c30ed1ee',
                                    f_path='/'))

        response.mustcontain("""<span style="text-transform: uppercase;"><a href="#">Branch: git</a></span>""")

    def test_index_paging(self):
        self.log_user()

        for r in [(73, 'a066b25d5df7016b45a41b7e2a78c33b57adc235'),
                  (92, 'cc66b61b8455b264a7a8a2d8ddc80fcfc58c221e'),
                  (109, '75feb4c33e81186c87eac740cee2447330288412'),
                  (1, '3d8f361e72ab303da48d799ff1ac40d5ac37c67e'),
                  (0, 'b986218ba1c9b0d6a259fac9b050b1724ed8e545')]:

            response = self.app.get(url(controller='files', action='index',
                                    repo_name=HG_REPO,
                                    revision=r[1],
                                    f_path='/'))

            response.mustcontain("""@ r%s:%s""" % (r[0], r[1][:12]))

    def test_file_source(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='index',
                                    repo_name=HG_REPO,
                                    revision='8911406ad776fdd3d0b9932a2e89677e57405a48',
                                    f_path='vcs/nodes.py'))

        response.mustcontain("""<div class="commit">Partially implemented <a class="issue-tracker-link" href="https://myissueserver.com/vcs_test_hg/issue/16">#16</a>. filecontent/commit message/author/node name are safe_unicode now.
In addition some other __str__ are unicode as well
Added test for unicode
Improved test to clone into uniq repository.
removed extra unicode conversion in diff.</div>
""")

        response.mustcontain("""<span style="text-transform: uppercase;"><a href="#">Branch: default</a></span>""")

    def test_file_source_history(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='history',
                                    repo_name=HG_REPO,
                                    revision='27cd5cce30c96924232dffcd24178a07ffeb5dfc',
                                    f_path='vcs/nodes.py'),
                                extra_environ={'HTTP_X_PARTIAL_XHR': '1'},)
        #test or history
        response.mustcontain("""<optgroup label="Changesets">
<option value="dbec37a0d5cab8ff39af4cfc4a4cd3996e4acfc6">r648:dbec37a0d5ca (default)</option>
<option value="1d20ed9eda9482d46ff0a6af5812550218b3ff15">r639:1d20ed9eda94 (default)</option>
<option value="0173395e822797f098799ed95c1a81b6a547a9ad">r547:0173395e8227 (default)</option>
<option value="afbb45ade933a8182f1d8ec5d4d1bb2de2572043">r546:afbb45ade933 (default)</option>
<option value="6f093e30cac34e6b4b11275a9f22f80c5d7ad1f7">r502:6f093e30cac3 (default)</option>
<option value="c7e2212dd2ae975d1d06534a3d7e317165c06960">r476:c7e2212dd2ae (default)</option>
<option value="45477506df79f701bf69419aac3e1f0fed3c5bcf">r472:45477506df79 (default)</option>
<option value="5fc76cb25d11e07c60de040f78b8cd265ff10d53">r469:5fc76cb25d11 (default)</option>
<option value="b073433cf8994969ee5cd7cce84cbe587bb880b2">r468:b073433cf899 (default)</option>
<option value="7a74dbfcacd1dbcb58bb9c860b2f29fbb22c4c96">r467:7a74dbfcacd1 (default)</option>
<option value="71ee52cc4d629096bdbee036325975dac2af4501">r465:71ee52cc4d62 (default)</option>
<option value="a5b217d26c5f111e72bae4de672b084ee0fbf75c">r452:a5b217d26c5f (default)</option>
<option value="47aedd538bf616eedcb0e7d630ea476df0e159c7">r450:47aedd538bf6 (default)</option>
<option value="8e4915fa32d727dcbf09746f637a5f82e539511e">r432:8e4915fa32d7 (default)</option>
<option value="25213a5fbb048dff8ba65d21e466a835536e5b70">r356:25213a5fbb04 (default)</option>
<option value="23debcedddc1c23c14be33e713e7786d4a9de471">r351:23debcedddc1 (default)</option>
<option value="61e25b2a90a19e7fffd75dea1e4c7e20df526bbe">r342:61e25b2a90a1 (default)</option>
<option value="fb95b340e0d03fa51f33c56c991c08077c99303e">r318:fb95b340e0d0 (webvcs)</option>
<option value="bda35e0e564fbbc5cd26fe0a37fb647a254c99fe">r303:bda35e0e564f (default)</option>
<option value="97ff74896d7dbf3115a337a421d44b55154acc89">r302:97ff74896d7d (default)</option>
<option value="cec3473c3fdb9599c98067182a075b49bde570f9">r293:cec3473c3fdb (default)</option>
<option value="0e86c43eef866a013a587666a877c879899599bb">r289:0e86c43eef86 (default)</option>
<option value="91a27c312808100cf20a602f78befbbff9d89bfd">r288:91a27c312808 (default)</option>
<option value="400e36a1670a57d11e3edcb5b07bf82c30006d0b">r287:400e36a1670a (default)</option>
<option value="014fb17dfc95b0995e838c565376bf9a993e230a">r261:014fb17dfc95 (default)</option>
<option value="cca7aebbc4d6125798446b11e69dc8847834a982">r260:cca7aebbc4d6 (default)</option>
<option value="14cdb2957c011a5feba36f50d960d9832ba0f0c1">r258:14cdb2957c01 (workdir)</option>
<option value="34df20118ed74b5987d22a579e8a60e903da5bf8">r245:34df20118ed7 (default)</option>
<option value="0375d9042a64a1ac1641528f0f0668f9a339e86d">r233:0375d9042a64 (workdir)</option>
<option value="94aa45fc1806c04d4ba640933edf682c22478453">r222:94aa45fc1806 (workdir)</option>
<option value="7ed99bc738818879941e3ce20243f8856a7cfc84">r188:7ed99bc73881 (default)</option>
<option value="1e85975528bcebe853732a9e5fb8dbf4461f6bb2">r184:1e85975528bc (default)</option>
<option value="ed30beddde7bbddb26042625be19bcd11576c1dd">r183:ed30beddde7b (default)</option>
<option value="a6664e18181c6fc81b751a8d01474e7e1a3fe7fc">r177:a6664e18181c (default)</option>
<option value="8911406ad776fdd3d0b9932a2e89677e57405a48">r167:8911406ad776 (default)</option>
<option value="aa957ed78c35a1541f508d2ec90e501b0a9e3167">r165:aa957ed78c35 (default)</option>
<option value="48e11b73e94c0db33e736eaeea692f990cb0b5f1">r140:48e11b73e94c (default)</option>
<option value="adf3cbf483298563b968a6c673cd5bde5f7d5eea">r126:adf3cbf48329 (default)</option>
<option value="6249fd0fb2cfb1411e764129f598e2cf0de79a6f">r113:6249fd0fb2cf (git)</option>
<option value="75feb4c33e81186c87eac740cee2447330288412">r109:75feb4c33e81 (default)</option>
<option value="9a4dc232ecdc763ef2e98ae2238cfcbba4f6ad8d">r108:9a4dc232ecdc (default)</option>
<option value="595cce4efa21fda2f2e4eeb4fe5f2a6befe6fa2d">r107:595cce4efa21 (default)</option>
<option value="4a8bd421fbc2dfbfb70d85a3fe064075ab2c49da">r104:4a8bd421fbc2 (default)</option>
<option value="57be63fc8f85e65a0106a53187f7316f8c487ffa">r102:57be63fc8f85 (default)</option>
<option value="5530bd87f7e2e124a64d07cb2654c997682128be">r101:5530bd87f7e2 (git)</option>
<option value="e516008b1c93f142263dc4b7961787cbad654ce1">r99:e516008b1c93 (default)</option>
<option value="41f43fc74b8b285984554532eb105ac3be5c434f">r93:41f43fc74b8b (default)</option>
<option value="cc66b61b8455b264a7a8a2d8ddc80fcfc58c221e">r92:cc66b61b8455 (default)</option>
<option value="73ab5b616b3271b0518682fb4988ce421de8099f">r91:73ab5b616b32 (default)</option>
<option value="e0da75f308c0f18f98e9ce6257626009fdda2b39">r82:e0da75f308c0 (default)</option>
<option value="fb2e41e0f0810be4d7103bc2a4c7be16ee3ec611">r81:fb2e41e0f081 (default)</option>
<option value="602ae2f5e7ade70b3b66a58cdd9e3e613dc8a028">r76:602ae2f5e7ad (default)</option>
<option value="a066b25d5df7016b45a41b7e2a78c33b57adc235">r73:a066b25d5df7 (default)</option>
<option value="637a933c905958ce5151f154147c25c1c7b68832">r61:637a933c9059 (web)</option>
<option value="0c21004effeb8ce2d2d5b4a8baf6afa8394b6fbc">r60:0c21004effeb (web)</option>
<option value="a1f39c56d3f1d52d5fb5920370a2a2716cd9a444">r59:a1f39c56d3f1 (web)</option>
<option value="97d32df05c715a3bbf936bf3cc4e32fb77fe1a7f">r58:97d32df05c71 (web)</option>
<option value="08eaf14517718dccea4b67755a93368341aca919">r57:08eaf1451771 (web)</option>
<option value="22f71ad265265a53238359c883aa976e725aa07d">r56:22f71ad26526 (web)</option>
<option value="97501f02b7b4330924b647755663a2d90a5e638d">r49:97501f02b7b4 (web)</option>
<option value="86ede6754f2b27309452bb11f997386ae01d0e5a">r47:86ede6754f2b (web)</option>
<option value="014c40c0203c423dc19ecf94644f7cac9d4cdce0">r45:014c40c0203c (web)</option>
<option value="ee87846a61c12153b51543bf860e1026c6d3dcba">r30:ee87846a61c1 (default)</option>
<option value="9bb326a04ae5d98d437dece54be04f830cf1edd9">r26:9bb326a04ae5 (default)</option>
<option value="536c1a19428381cfea92ac44985304f6a8049569">r24:536c1a194283 (default)</option>
<option value="dc5d2c0661b61928834a785d3e64a3f80d3aad9c">r8:dc5d2c0661b6 (default)</option>
<option value="3803844fdbd3b711175fc3da9bdacfcd6d29a6fb">r7:3803844fdbd3 (default)</option>
</optgroup>
<optgroup label="Branches">
<option value="96507bd11ecc815ebc6270fdf6db110928c09c1e">default</option>
<option value="4f7e2131323e0749a740c0a56ab68ae9269c562a">stable</option>
</optgroup>
<optgroup label="Tags">
<option value="2c96c02def9a7c997f33047761a53943e6254396">v0.2.0</option>
<option value="8680b1d1cee3aa3c1ab3734b76ee164bbedbc5c9">v0.1.9</option>
<option value="ecb25ba9c96faf1e65a0bc3fd914918420a2f116">v0.1.8</option>
<option value="f67633a2894edaf28513706d558205fa93df9209">v0.1.7</option>
<option value="02b38c0eb6f982174750c0e309ff9faddc0c7e12">v0.1.6</option>
<option value="a6664e18181c6fc81b751a8d01474e7e1a3fe7fc">v0.1.5</option>
<option value="fd4bdb5e9b2a29b4393a4ac6caef48c17ee1a200">v0.1.4</option>
<option value="17544fbfcd33ffb439e2b728b5d526b1ef30bfcf">v0.1.3</option>
<option value="a7e60bff65d57ac3a1a1ce3b12a70f8a9e8a7720">v0.1.2</option>
<option value="fef5bfe1dc17611d5fb59a7f6f95c55c3606f933">v0.1.11</option>
<option value="92831aebf2f8dd4879e897024b89d09af214df1c">v0.1.10</option>
<option value="eb3a60fc964309c1a318b8dfe26aa2d1586c85ae">v0.1.1</option>
<option value="96507bd11ecc815ebc6270fdf6db110928c09c1e">tip</option>
</optgroup>
""")

    def test_file_annotation(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='index',
                                    repo_name=HG_REPO,
                                    revision='27cd5cce30c96924232dffcd24178a07ffeb5dfc',
                                    f_path='vcs/nodes.py',
                                    annotate=True))

        response.mustcontain("""<span style="text-transform: uppercase;"><a href="#">Branch: default</a></span>""")

    def test_file_annotation_history(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='history',
                                    repo_name=HG_REPO,
                                    revision='27cd5cce30c96924232dffcd24178a07ffeb5dfc',
                                    f_path='vcs/nodes.py',
                                    annotate=True),
                                extra_environ={'HTTP_X_PARTIAL_XHR': '1'})

        response.mustcontain("""
<option value="dbec37a0d5cab8ff39af4cfc4a4cd3996e4acfc6">r648:dbec37a0d5ca (default)</option>
<option value="1d20ed9eda9482d46ff0a6af5812550218b3ff15">r639:1d20ed9eda94 (default)</option>
<option value="0173395e822797f098799ed95c1a81b6a547a9ad">r547:0173395e8227 (default)</option>
<option value="afbb45ade933a8182f1d8ec5d4d1bb2de2572043">r546:afbb45ade933 (default)</option>
<option value="6f093e30cac34e6b4b11275a9f22f80c5d7ad1f7">r502:6f093e30cac3 (default)</option>
<option value="c7e2212dd2ae975d1d06534a3d7e317165c06960">r476:c7e2212dd2ae (default)</option>
<option value="45477506df79f701bf69419aac3e1f0fed3c5bcf">r472:45477506df79 (default)</option>
<option value="5fc76cb25d11e07c60de040f78b8cd265ff10d53">r469:5fc76cb25d11 (default)</option>
<option value="b073433cf8994969ee5cd7cce84cbe587bb880b2">r468:b073433cf899 (default)</option>
<option value="7a74dbfcacd1dbcb58bb9c860b2f29fbb22c4c96">r467:7a74dbfcacd1 (default)</option>
<option value="71ee52cc4d629096bdbee036325975dac2af4501">r465:71ee52cc4d62 (default)</option>
<option value="a5b217d26c5f111e72bae4de672b084ee0fbf75c">r452:a5b217d26c5f (default)</option>
<option value="47aedd538bf616eedcb0e7d630ea476df0e159c7">r450:47aedd538bf6 (default)</option>
<option value="8e4915fa32d727dcbf09746f637a5f82e539511e">r432:8e4915fa32d7 (default)</option>
<option value="25213a5fbb048dff8ba65d21e466a835536e5b70">r356:25213a5fbb04 (default)</option>
<option value="23debcedddc1c23c14be33e713e7786d4a9de471">r351:23debcedddc1 (default)</option>
<option value="61e25b2a90a19e7fffd75dea1e4c7e20df526bbe">r342:61e25b2a90a1 (default)</option>
<option value="fb95b340e0d03fa51f33c56c991c08077c99303e">r318:fb95b340e0d0 (webvcs)</option>
<option value="bda35e0e564fbbc5cd26fe0a37fb647a254c99fe">r303:bda35e0e564f (default)</option>
<option value="97ff74896d7dbf3115a337a421d44b55154acc89">r302:97ff74896d7d (default)</option>
<option value="cec3473c3fdb9599c98067182a075b49bde570f9">r293:cec3473c3fdb (default)</option>
<option value="0e86c43eef866a013a587666a877c879899599bb">r289:0e86c43eef86 (default)</option>
<option value="91a27c312808100cf20a602f78befbbff9d89bfd">r288:91a27c312808 (default)</option>
<option value="400e36a1670a57d11e3edcb5b07bf82c30006d0b">r287:400e36a1670a (default)</option>
<option value="014fb17dfc95b0995e838c565376bf9a993e230a">r261:014fb17dfc95 (default)</option>
<option value="cca7aebbc4d6125798446b11e69dc8847834a982">r260:cca7aebbc4d6 (default)</option>
<option value="14cdb2957c011a5feba36f50d960d9832ba0f0c1">r258:14cdb2957c01 (workdir)</option>
<option value="34df20118ed74b5987d22a579e8a60e903da5bf8">r245:34df20118ed7 (default)</option>
<option value="0375d9042a64a1ac1641528f0f0668f9a339e86d">r233:0375d9042a64 (workdir)</option>
<option value="94aa45fc1806c04d4ba640933edf682c22478453">r222:94aa45fc1806 (workdir)</option>
<option value="7ed99bc738818879941e3ce20243f8856a7cfc84">r188:7ed99bc73881 (default)</option>
<option value="1e85975528bcebe853732a9e5fb8dbf4461f6bb2">r184:1e85975528bc (default)</option>
<option value="ed30beddde7bbddb26042625be19bcd11576c1dd">r183:ed30beddde7b (default)</option>
<option value="a6664e18181c6fc81b751a8d01474e7e1a3fe7fc">r177:a6664e18181c (default)</option>
<option value="8911406ad776fdd3d0b9932a2e89677e57405a48">r167:8911406ad776 (default)</option>
<option value="aa957ed78c35a1541f508d2ec90e501b0a9e3167">r165:aa957ed78c35 (default)</option>
<option value="48e11b73e94c0db33e736eaeea692f990cb0b5f1">r140:48e11b73e94c (default)</option>
<option value="adf3cbf483298563b968a6c673cd5bde5f7d5eea">r126:adf3cbf48329 (default)</option>
<option value="6249fd0fb2cfb1411e764129f598e2cf0de79a6f">r113:6249fd0fb2cf (git)</option>
<option value="75feb4c33e81186c87eac740cee2447330288412">r109:75feb4c33e81 (default)</option>
<option value="9a4dc232ecdc763ef2e98ae2238cfcbba4f6ad8d">r108:9a4dc232ecdc (default)</option>
<option value="595cce4efa21fda2f2e4eeb4fe5f2a6befe6fa2d">r107:595cce4efa21 (default)</option>
<option value="4a8bd421fbc2dfbfb70d85a3fe064075ab2c49da">r104:4a8bd421fbc2 (default)</option>
<option value="57be63fc8f85e65a0106a53187f7316f8c487ffa">r102:57be63fc8f85 (default)</option>
<option value="5530bd87f7e2e124a64d07cb2654c997682128be">r101:5530bd87f7e2 (git)</option>
<option value="e516008b1c93f142263dc4b7961787cbad654ce1">r99:e516008b1c93 (default)</option>
<option value="41f43fc74b8b285984554532eb105ac3be5c434f">r93:41f43fc74b8b (default)</option>
<option value="cc66b61b8455b264a7a8a2d8ddc80fcfc58c221e">r92:cc66b61b8455 (default)</option>
<option value="73ab5b616b3271b0518682fb4988ce421de8099f">r91:73ab5b616b32 (default)</option>
<option value="e0da75f308c0f18f98e9ce6257626009fdda2b39">r82:e0da75f308c0 (default)</option>
<option value="fb2e41e0f0810be4d7103bc2a4c7be16ee3ec611">r81:fb2e41e0f081 (default)</option>
<option value="602ae2f5e7ade70b3b66a58cdd9e3e613dc8a028">r76:602ae2f5e7ad (default)</option>
<option value="a066b25d5df7016b45a41b7e2a78c33b57adc235">r73:a066b25d5df7 (default)</option>
<option value="637a933c905958ce5151f154147c25c1c7b68832">r61:637a933c9059 (web)</option>
<option value="0c21004effeb8ce2d2d5b4a8baf6afa8394b6fbc">r60:0c21004effeb (web)</option>
<option value="a1f39c56d3f1d52d5fb5920370a2a2716cd9a444">r59:a1f39c56d3f1 (web)</option>
<option value="97d32df05c715a3bbf936bf3cc4e32fb77fe1a7f">r58:97d32df05c71 (web)</option>
<option value="08eaf14517718dccea4b67755a93368341aca919">r57:08eaf1451771 (web)</option>
<option value="22f71ad265265a53238359c883aa976e725aa07d">r56:22f71ad26526 (web)</option>
<option value="97501f02b7b4330924b647755663a2d90a5e638d">r49:97501f02b7b4 (web)</option>
<option value="86ede6754f2b27309452bb11f997386ae01d0e5a">r47:86ede6754f2b (web)</option>
<option value="014c40c0203c423dc19ecf94644f7cac9d4cdce0">r45:014c40c0203c (web)</option>
<option value="ee87846a61c12153b51543bf860e1026c6d3dcba">r30:ee87846a61c1 (default)</option>
<option value="9bb326a04ae5d98d437dece54be04f830cf1edd9">r26:9bb326a04ae5 (default)</option>
<option value="536c1a19428381cfea92ac44985304f6a8049569">r24:536c1a194283 (default)</option>
<option value="dc5d2c0661b61928834a785d3e64a3f80d3aad9c">r8:dc5d2c0661b6 (default)</option>
<option value="3803844fdbd3b711175fc3da9bdacfcd6d29a6fb">r7:3803844fdbd3 (default)</option>
</optgroup>
<optgroup label="Branches">
<option value="96507bd11ecc815ebc6270fdf6db110928c09c1e">default</option>
<option value="4f7e2131323e0749a740c0a56ab68ae9269c562a">stable</option>
</optgroup>
<optgroup label="Tags">
<option value="2c96c02def9a7c997f33047761a53943e6254396">v0.2.0</option>
<option value="8680b1d1cee3aa3c1ab3734b76ee164bbedbc5c9">v0.1.9</option>
<option value="ecb25ba9c96faf1e65a0bc3fd914918420a2f116">v0.1.8</option>
<option value="f67633a2894edaf28513706d558205fa93df9209">v0.1.7</option>
<option value="02b38c0eb6f982174750c0e309ff9faddc0c7e12">v0.1.6</option>
<option value="a6664e18181c6fc81b751a8d01474e7e1a3fe7fc">v0.1.5</option>
<option value="fd4bdb5e9b2a29b4393a4ac6caef48c17ee1a200">v0.1.4</option>
<option value="17544fbfcd33ffb439e2b728b5d526b1ef30bfcf">v0.1.3</option>
<option value="a7e60bff65d57ac3a1a1ce3b12a70f8a9e8a7720">v0.1.2</option>
<option value="fef5bfe1dc17611d5fb59a7f6f95c55c3606f933">v0.1.11</option>
<option value="92831aebf2f8dd4879e897024b89d09af214df1c">v0.1.10</option>
<option value="eb3a60fc964309c1a318b8dfe26aa2d1586c85ae">v0.1.1</option>
<option value="96507bd11ecc815ebc6270fdf6db110928c09c1e">tip</option>
</optgroup>""")

    def test_file_annotation_git(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='index',
                                    repo_name=GIT_REPO,
                                    revision='master',
                                    f_path='vcs/nodes.py',
                                    annotate=True))

    def test_archival(self):
        self.log_user()
        _set_downloads(HG_REPO, set_to=True)
        for arch_ext, info in ARCHIVE_SPECS.items():
            short = '27cd5cce30c9%s' % arch_ext
            fname = '27cd5cce30c96924232dffcd24178a07ffeb5dfc%s' % arch_ext
            filename = '%s-%s' % (HG_REPO, short)
            response = self.app.get(url(controller='files',
                                        action='archivefile',
                                        repo_name=HG_REPO,
                                        fname=fname))

            self.assertEqual(response.status, '200 OK')
            heads = [
                ('Pragma', 'no-cache'),
                ('Cache-Control', 'no-cache'),
                ('Content-Disposition', 'attachment; filename=%s' % filename),
                ('Content-Type', '%s; charset=utf-8' % info[0]),
            ]
            self.assertEqual(response.response._headers.items(), heads)

    def test_archival_wrong_ext(self):
        self.log_user()
        _set_downloads(HG_REPO, set_to=True)
        for arch_ext in ['tar', 'rar', 'x', '..ax', '.zipz']:
            fname = '27cd5cce30c96924232dffcd24178a07ffeb5dfc%s' % arch_ext

            response = self.app.get(url(controller='files',
                                        action='archivefile',
                                        repo_name=HG_REPO,
                                        fname=fname))
            response.mustcontain('Unknown archive type')

    def test_archival_wrong_revision(self):
        self.log_user()
        _set_downloads(HG_REPO, set_to=True)
        for rev in ['00x000000', 'tar', 'wrong', '@##$@$42413232', '232dffcd']:
            fname = '%s.zip' % rev

            response = self.app.get(url(controller='files',
                                        action='archivefile',
                                        repo_name=HG_REPO,
                                        fname=fname))
            response.mustcontain('Unknown revision')

    #==========================================================================
    # RAW FILE
    #==========================================================================
    def test_raw_file_ok(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='rawfile',
                                    repo_name=HG_REPO,
                                    revision='27cd5cce30c96924232dffcd24178a07ffeb5dfc',
                                    f_path='vcs/nodes.py'))

        self.assertEqual(response.content_disposition, "attachment; filename=nodes.py")
        self.assertEqual(response.content_type, "text/x-python")

    def test_raw_file_wrong_cs(self):
        self.log_user()
        rev = u'ERRORce30c96924232dffcd24178a07ffeb5dfc'
        f_path = 'vcs/nodes.py'

        response = self.app.get(url(controller='files', action='rawfile',
                                    repo_name=HG_REPO,
                                    revision=rev,
                                    f_path=f_path), status=404)

        msg = """Revision %s does not exist for this repository""" % (rev)
        response.mustcontain(msg)

    def test_raw_file_wrong_f_path(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        f_path = 'vcs/ERRORnodes.py'
        response = self.app.get(url(controller='files', action='rawfile',
                                    repo_name=HG_REPO,
                                    revision=rev,
                                    f_path=f_path), status=404)

        msg = "There is no file nor directory at the given path: &#39;%s&#39; at revision %s" % (f_path, rev[:12])
        response.mustcontain(msg)

    #==========================================================================
    # RAW RESPONSE - PLAIN
    #==========================================================================
    def test_raw_ok(self):
        self.log_user()
        response = self.app.get(url(controller='files', action='raw',
                                    repo_name=HG_REPO,
                                    revision='27cd5cce30c96924232dffcd24178a07ffeb5dfc',
                                    f_path='vcs/nodes.py'))

        self.assertEqual(response.content_type, "text/plain")

    def test_raw_wrong_cs(self):
        self.log_user()
        rev = u'ERRORcce30c96924232dffcd24178a07ffeb5dfc'
        f_path = 'vcs/nodes.py'

        response = self.app.get(url(controller='files', action='raw',
                                    repo_name=HG_REPO,
                                    revision=rev,
                                    f_path=f_path), status=404)

        msg = """Revision %s does not exist for this repository""" % (rev)
        response.mustcontain(msg)

    def test_raw_wrong_f_path(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        f_path = 'vcs/ERRORnodes.py'
        response = self.app.get(url(controller='files', action='raw',
                                    repo_name=HG_REPO,
                                    revision=rev,
                                    f_path=f_path), status=404)
        msg = "There is no file nor directory at the given path: &#39;%s&#39; at revision %s" % (f_path, rev[:12])
        response.mustcontain(msg)

    def test_ajaxed_files_list(self):
        self.log_user()
        rev = '27cd5cce30c96924232dffcd24178a07ffeb5dfc'
        response = self.app.get(
            url('files_nodelist_home', repo_name=HG_REPO, f_path='/',
                revision=rev),
            extra_environ={'HTTP_X_PARTIAL_XHR': '1'},
        )
        response.mustcontain("vcs/web/simplevcs/views/repository.py")

    #HG - ADD FILE
    def test_add_file_view_hg(self):
        self.log_user()
        response = self.app.get(url('files_add_home',
                                      repo_name=HG_REPO,
                                      revision='tip', f_path='/'))

    def test_add_file_into_hg_missing_content(self):
        self.log_user()
        response = self.app.post(url('files_add_home',
                                      repo_name=HG_REPO,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': ''
                                 },
                                 status=302)

        self.checkSessionFlash(response, 'No content')

    def test_add_file_into_hg_missing_filename(self):
        self.log_user()
        response = self.app.post(url('files_add_home',
                                      repo_name=HG_REPO,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "foo"
                                 },
                                 status=302)

        self.checkSessionFlash(response, 'No filename')

    @parameterized.expand([
        ('/abs', 'foo'),
        ('../rel', 'foo'),
        ('file/../foo', 'foo'),
    ])
    def test_add_file_into_hg_bad_filenames(self, location, filename):
        self.log_user()
        response = self.app.post(url('files_add_home',
                                      repo_name=HG_REPO,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "foo",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)

        self.checkSessionFlash(response, 'Location must be relative path and must not contain .. in path')

    @parameterized.expand([
        (1, '', 'foo.txt'),
        (2, 'dir', 'foo.rst'),
        (3, 'rel/dir', 'foo.bar'),
    ])
    def test_add_file_into_hg(self, cnt, location, filename):
        self.log_user()
        repo = fixture.create_repo('commit-test-%s' % cnt, repo_type='hg')
        response = self.app.post(url('files_add_home',
                                      repo_name=repo.repo_name,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "foo",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)
        try:
            self.checkSessionFlash(response, 'Successfully committed to %s'
                                   % os.path.join(location, filename))
        finally:
            fixture.destroy_repo(repo.repo_name)

    ##GIT - ADD FILE
    def test_add_file_view_git(self):
        self.log_user()
        response = self.app.get(url('files_add_home',
                                      repo_name=GIT_REPO,
                                      revision='tip', f_path='/'))

    def test_add_file_into_git_missing_content(self):
        self.log_user()
        response = self.app.post(url('files_add_home',
                                      repo_name=GIT_REPO,
                                      revision='tip', f_path='/'),
                                 params={
                                    ''
                                 },
                                 status=302)

        self.checkSessionFlash(response, 'No content')

    def test_add_file_into_git_missing_filename(self):
        self.log_user()
        response = self.app.post(url('files_add_home',
                                      repo_name=GIT_REPO,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "foo"
                                 },
                                 status=302)

        self.checkSessionFlash(response, 'No filename')

    @parameterized.expand([
        ('/abs', 'foo'),
        ('../rel', 'foo'),
        ('file/../foo', 'foo'),
    ])
    def test_add_file_into_git_bad_filenames(self, location, filename):
        self.log_user()
        response = self.app.post(url('files_add_home',
                                      repo_name=GIT_REPO,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "foo",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)

        self.checkSessionFlash(response, 'Location must be relative path and must not contain .. in path')

    @parameterized.expand([
        (1, '', 'foo.txt'),
        (2, 'dir', 'foo.rst'),
        (3, 'rel/dir', 'foo.bar'),
    ])
    def test_add_file_into_git(self, cnt, location, filename):
        self.log_user()
        repo = fixture.create_repo('commit-test-%s' % cnt, repo_type='git')
        response = self.app.post(url('files_add_home',
                                      repo_name=repo.repo_name,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "foo",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)
        try:
            self.checkSessionFlash(response, 'Successfully committed to %s'
                                   % os.path.join(location, filename))
        finally:
            fixture.destroy_repo(repo.repo_name)

    #HG - EDIT
    def test_edit_file_view_hg(self):
        self.log_user()
        response = self.app.get(url('files_edit_home',
                                      repo_name=HG_REPO,
                                      revision='tip', f_path='vcs/nodes.py'))

    def test_edit_file_view_not_on_branch_hg(self):
        self.log_user()
        repo = fixture.create_repo('test-edit-repo', repo_type='hg')

        ## add file
        location = 'vcs'
        filename = 'nodes.py'
        response = self.app.post(url('files_add_home',
                                      repo_name=repo.repo_name,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "def py():\n print 'hello'\n",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)
        response.follow()
        try:
            self.checkSessionFlash(response, 'Successfully committed to %s'
                                   % os.path.join(location, filename))
            response = self.app.get(url('files_edit_home',
                                          repo_name=repo.repo_name,
                                          revision='tip', f_path='vcs/nodes.py'),
                                    status=302)
            self.checkSessionFlash(response,
                'You can only edit files with revision being a valid branch')
        finally:
            fixture.destroy_repo(repo.repo_name)

    def test_edit_file_view_commit_changes_hg(self):
        self.log_user()
        repo = fixture.create_repo('test-edit-repo', repo_type='hg')

        ## add file
        location = 'vcs'
        filename = 'nodes.py'
        response = self.app.post(url('files_add_home',
                                      repo_name=repo.repo_name,
                                      revision='tip',
                                      f_path='/'),
                                 params={
                                    'content': "def py():\n print 'hello'\n",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)
        response.follow()
        try:
            self.checkSessionFlash(response, 'Successfully committed to %s'
                                   % os.path.join(location, filename))
            response = self.app.post(url('files_edit_home',
                                          repo_name=repo.repo_name,
                                          revision=repo.scm_instance.DEFAULT_BRANCH_NAME,
                                          f_path='vcs/nodes.py'),
                                     params={
                                        'content': "def py():\n print 'hello world'\n",
                                        'message': 'i commited',
                                     },
                                    status=302)
            self.checkSessionFlash(response,
                                   'Successfully committed to vcs/nodes.py')
        finally:
            fixture.destroy_repo(repo.repo_name)

    #GIT - EDIT
    def test_edit_file_view_git(self):
        self.log_user()
        response = self.app.get(url('files_edit_home',
                                      repo_name=GIT_REPO,
                                      revision='tip', f_path='vcs/nodes.py'))

    def test_edit_file_view_not_on_branch_git(self):
        self.log_user()
        repo = fixture.create_repo('test-edit-repo', repo_type='git')

        ## add file
        location = 'vcs'
        filename = 'nodes.py'
        response = self.app.post(url('files_add_home',
                                      repo_name=repo.repo_name,
                                      revision='tip', f_path='/'),
                                 params={
                                    'content': "def py():\n print 'hello'\n",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)
        response.follow()
        try:
            self.checkSessionFlash(response, 'Successfully committed to %s'
                                   % os.path.join(location, filename))
            response = self.app.get(url('files_edit_home',
                                          repo_name=repo.repo_name,
                                          revision='tip', f_path='vcs/nodes.py'),
                                    status=302)
            self.checkSessionFlash(response,
                'You can only edit files with revision being a valid branch')
        finally:
            fixture.destroy_repo(repo.repo_name)

    def test_edit_file_view_commit_changes_git(self):
        self.log_user()
        repo = fixture.create_repo('test-edit-repo', repo_type='git')

        ## add file
        location = 'vcs'
        filename = 'nodes.py'
        response = self.app.post(url('files_add_home',
                                      repo_name=repo.repo_name,
                                      revision='tip',
                                      f_path='/'),
                                 params={
                                    'content': "def py():\n print 'hello'\n",
                                    'filename': filename,
                                    'location': location
                                 },
                                 status=302)
        response.follow()
        try:
            self.checkSessionFlash(response, 'Successfully committed to %s'
                                   % os.path.join(location, filename))
            response = self.app.post(url('files_edit_home',
                                          repo_name=repo.repo_name,
                                          revision=repo.scm_instance.DEFAULT_BRANCH_NAME,
                                          f_path='vcs/nodes.py'),
                                     params={
                                        'content': "def py():\n print 'hello world'\n",
                                        'message': 'i commited',
                                     },
                                    status=302)
            self.checkSessionFlash(response,
                                   'Successfully committed to vcs/nodes.py')
        finally:
            fixture.destroy_repo(repo.repo_name)
