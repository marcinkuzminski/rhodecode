from rhodecode.tests import *
from rhodecode.tests.api.api_base import BaseTestApi


class TestHgApi(BaseTestApi, TestController):
    REPO = HG_REPO
    REPO_TYPE = 'hg'
