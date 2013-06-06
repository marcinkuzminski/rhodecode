from rhodecode.tests import *


class TestTagsController(TestController):

    def test_index_hg(self):
        self.log_user()
        response = self.app.get(url(controller='tags', action='index', repo_name=HG_REPO))
        response.mustcontain("""<a href="/%s/files/96507bd11ecc815ebc6270fdf6db110928c09c1e/">tip</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/2c96c02def9a7c997f33047761a53943e6254396/">v0.2.0</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/fef5bfe1dc17611d5fb59a7f6f95c55c3606f933/">v0.1.11</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/92831aebf2f8dd4879e897024b89d09af214df1c/">v0.1.10</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/8680b1d1cee3aa3c1ab3734b76ee164bbedbc5c9/">v0.1.9</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/ecb25ba9c96faf1e65a0bc3fd914918420a2f116/">v0.1.8</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/f67633a2894edaf28513706d558205fa93df9209/">v0.1.7</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/02b38c0eb6f982174750c0e309ff9faddc0c7e12/">v0.1.6</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/a6664e18181c6fc81b751a8d01474e7e1a3fe7fc/">v0.1.5</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/fd4bdb5e9b2a29b4393a4ac6caef48c17ee1a200/">v0.1.4</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/17544fbfcd33ffb439e2b728b5d526b1ef30bfcf/">v0.1.3</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/a7e60bff65d57ac3a1a1ce3b12a70f8a9e8a7720/">v0.1.2</a>""" % HG_REPO)
        response.mustcontain("""<a href="/%s/files/eb3a60fc964309c1a318b8dfe26aa2d1586c85ae/">v0.1.1</a>""" % HG_REPO)

    def test_index_git(self):
        self.log_user()
        response = self.app.get(url(controller='tags', action='index', repo_name=GIT_REPO))

        response.mustcontain("""<a href="/%s/files/137fea89f304a42321d40488091ee2ed419a3686/">v0.2.2</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/5051d0fa344d4408a2659d9a0348eb2d41868ecf/">v0.2.1</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/599ba911aa24d2981225f3966eb659dfae9e9f30/">v0.2.0</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/c60f01b77c42dce653d6b1d3b04689862c261929/">v0.1.11</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/10cddef6b794696066fb346434014f0a56810218/">v0.1.10</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/341d28f0eec5ddf0b6b77871e13c2bbd6bec685c/">v0.1.9</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/74ebce002c088b8a5ecf40073db09375515ecd68/">v0.1.8</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/4d78bf73b5c22c82b68f902f138f7881b4fffa2c/">v0.1.7</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/0205cb3f44223fb3099d12a77a69c81b798772d9/">v0.1.6</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/6c0ce52b229aa978889e91b38777f800e85f330b/">v0.1.5</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/7d735150934cd7645ac3051903add952390324a5/">v0.1.4</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/5a3a8fb005554692b16e21dee62bf02667d8dc3e/">v0.1.3</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/0ba5f8a4660034ff25c0cac2a5baabf5d2791d63/">v0.1.2</a>""" % GIT_REPO)
        response.mustcontain("""<a href="/%s/files/e6ea6d16e2f26250124a1f4b4fe37a912f9d86a0/">v0.1.1</a>""" % GIT_REPO)
