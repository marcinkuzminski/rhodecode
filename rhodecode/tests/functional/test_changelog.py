from rhodecode.tests import *


class TestChangelogController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO))

        response.mustcontain("""<div id="chg_20" class="container tablerow1">""")
        response.mustcontain(
            """<input class="changeset_range" id="5e204e7583b9" """
            """name="5e204e7583b9" type="checkbox" value="1" />"""
        )
        response.mustcontain(
            """<span class="changeset_id">154:"""
            """<span class="changeset_hash">5e204e7583b9</span></span>"""
        )

        response.mustcontain("""Small update at simplevcs app""")

        response.mustcontain(
            """<div id="5e204e7583b9c8e7b93a020bd036564b1e731dae"  """
            """style="float:right;" class="changed_total tooltip" """
            """title="Affected number of files, click to show """
            """more details">3</div>"""
        )

        #pagination
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':1})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':2})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':3})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':4})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':5})
        response = self.app.get(url(controller='changelog', action='index',
                                    repo_name=HG_REPO), {'page':6})

        # Test response after pagination...
        response.mustcontain(
            """<input class="changeset_range" id="46ad32a4f974" """
            """name="46ad32a4f974" type="checkbox" value="1" />"""
        )
        response.mustcontain(
            """<span class="changeset_id">64:"""
            """<span class="changeset_hash">46ad32a4f974</span></span>"""
        )

        response.mustcontain(
            """<div id="46ad32a4f974e45472a898c6b0acb600320579b1"  """
            """style="float:right;" class="changed_total tooltip" """
            """title="Affected number of files, click to show """
            """more details">21</div>"""
        )

        response.mustcontain(
            """<a href="/%s/changeset/"""
            """46ad32a4f974e45472a898c6b0acb600320579b1" """
            """title="Merge with 2e6a2bf9356ca56df08807f4ad86d480da72a8f4">"""
            """46ad32a4f974</a>""" % HG_REPO
        )
