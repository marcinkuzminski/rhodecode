from rhodecode.tests import *
from rhodecode.tests.api.api_base import BaseTestApi


class TestGitApi(BaseTestApi, TestController):
    REPO = GIT_REPO
    REPO_TYPE = 'git'
