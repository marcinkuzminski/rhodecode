"""Pylons application test package

This package assumes the Pylons environment is already loaded, such as
when this script is imported from the `nosetests --with-pylons=test.ini`
command.

This module initializes the application via ``websetup`` (`paster
setup-app`) and provides the base testing objects.

nosetests -x - fail on first error
nosetests rhodecode.tests.functional.test_admin_settings:TestSettingsController.test_my_account
nosetests --pdb --pdb-failures
nosetests --with-coverage --cover-package=rhodecode.model.validators rhodecode.tests.test_validators

optional FLAGS:
    RC_WHOOSH_TEST_DISABLE=1 - skip whoosh index building and tests
    RC_NO_TMP_PATH=1 - disable new temp path for tests, used mostly for test_vcs_operations

"""
import os
import time
import logging
import datetime
import hashlib
import tempfile
from os.path import join as jn

from unittest import TestCase
from tempfile import _RandomNameSequence

from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand

import pylons
import pylons.test
from pylons import config, url
from pylons.i18n.translation import _get_translator
from pylons.util import ContextObj

from routes.util import URLGenerator
from webtest import TestApp
from nose.plugins.skip import SkipTest

from rhodecode import is_windows
from rhodecode.model.meta import Session
from rhodecode.model.db import User
from rhodecode.tests.nose_parametrized import parameterized
from rhodecode.lib.utils2 import safe_unicode, safe_str


os.environ['TZ'] = 'UTC'
if not is_windows:
    time.tzset()

log = logging.getLogger(__name__)

__all__ = [
    'parameterized', 'environ', 'url', 'get_new_dir', 'TestController',
    'SkipTest', 'ldap_lib_installed', 'BaseTestCase', 'init_stack',
    'TESTS_TMP_PATH', 'HG_REPO', 'GIT_REPO', 'NEW_HG_REPO', 'NEW_GIT_REPO',
    'HG_FORK', 'GIT_FORK', 'TEST_USER_ADMIN_LOGIN', 'TEST_USER_ADMIN_PASS',
    'TEST_USER_REGULAR_LOGIN', 'TEST_USER_REGULAR_PASS',
    'TEST_USER_REGULAR_EMAIL', 'TEST_USER_REGULAR2_LOGIN',
    'TEST_USER_REGULAR2_PASS', 'TEST_USER_REGULAR2_EMAIL', 'TEST_HG_REPO',
    'TEST_HG_REPO_CLONE', 'TEST_HG_REPO_PULL', 'TEST_GIT_REPO',
    'TEST_GIT_REPO_CLONE', 'TEST_GIT_REPO_PULL', 'HG_REMOTE_REPO',
    'GIT_REMOTE_REPO', 'SCM_TESTS',
]

# Invoke websetup with the current config file
# SetupCommand('setup-app').run([config_file])

environ = {}

#SOME GLOBALS FOR TESTS

TESTS_TMP_PATH = jn('/', 'tmp', 'rc_test_%s' % _RandomNameSequence().next())
TEST_USER_ADMIN_LOGIN = 'test_admin'
TEST_USER_ADMIN_PASS = 'test12'
TEST_USER_ADMIN_EMAIL = 'test_admin@mail.com'

TEST_USER_REGULAR_LOGIN = 'test_regular'
TEST_USER_REGULAR_PASS = 'test12'
TEST_USER_REGULAR_EMAIL = 'test_regular@mail.com'

TEST_USER_REGULAR2_LOGIN = 'test_regular2'
TEST_USER_REGULAR2_PASS = 'test12'
TEST_USER_REGULAR2_EMAIL = 'test_regular2@mail.com'

HG_REPO = 'vcs_test_hg'
GIT_REPO = 'vcs_test_git'

NEW_HG_REPO = 'vcs_test_hg_new'
NEW_GIT_REPO = 'vcs_test_git_new'

HG_FORK = 'vcs_test_hg_fork'
GIT_FORK = 'vcs_test_git_fork'

## VCS
SCM_TESTS = ['hg', 'git']
uniq_suffix = str(int(time.mktime(datetime.datetime.now().timetuple())))

GIT_REMOTE_REPO = 'git://github.com/codeinn/vcs.git'

TEST_GIT_REPO = jn(TESTS_TMP_PATH, GIT_REPO)
TEST_GIT_REPO_CLONE = jn(TESTS_TMP_PATH, 'vcsgitclone%s' % uniq_suffix)
TEST_GIT_REPO_PULL = jn(TESTS_TMP_PATH, 'vcsgitpull%s' % uniq_suffix)


HG_REMOTE_REPO = 'http://bitbucket.org/marcinkuzminski/vcs'

TEST_HG_REPO = jn(TESTS_TMP_PATH, HG_REPO)
TEST_HG_REPO_CLONE = jn(TESTS_TMP_PATH, 'vcshgclone%s' % uniq_suffix)
TEST_HG_REPO_PULL = jn(TESTS_TMP_PATH, 'vcshgpull%s' % uniq_suffix)

TEST_DIR = tempfile.gettempdir()
TEST_REPO_PREFIX = 'vcs-test'

# cached repos if any !
# comment out to get some other repos from bb or github
GIT_REMOTE_REPO = jn(TESTS_TMP_PATH, GIT_REPO)
HG_REMOTE_REPO = jn(TESTS_TMP_PATH, HG_REPO)

#skip ldap tests if LDAP lib is not installed
ldap_lib_installed = False
try:
    import ldap
    ldap_lib_installed = True
except ImportError:
    # means that python-ldap is not installed
    pass


def get_new_dir(title):
    """
    Returns always new directory path.
    """
    from rhodecode.tests.vcs.utils import get_normalized_path
    name = TEST_REPO_PREFIX
    if title:
        name = '-'.join((name, title))
    hex = hashlib.sha1(str(time.time())).hexdigest()
    name = '-'.join((name, hex))
    path = os.path.join(TEST_DIR, name)
    return get_normalized_path(path)


def init_stack(config=None):
    if not config:
        config = pylons.test.pylonsapp.config
    url._push_object(URLGenerator(config['routes.map'], environ))
    pylons.app_globals._push_object(config['pylons.app_globals'])
    pylons.config._push_object(config)
    pylons.tmpl_context._push_object(ContextObj())
    # Initialize a translator for tests that utilize i18n
    translator = _get_translator(pylons.config.get('lang'))
    pylons.translator._push_object(translator)


class BaseTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        self.wsgiapp = pylons.test.pylonsapp
        init_stack(self.wsgiapp.config)
        TestCase.__init__(self, *args, **kwargs)


class TestController(BaseTestCase):

    def __init__(self, *args, **kwargs):
        BaseTestCase.__init__(self, *args, **kwargs)
        self.app = TestApp(self.wsgiapp)
        self.index_location = config['app_conf']['index_dir']

    def log_user(self, username=TEST_USER_ADMIN_LOGIN,
                 password=TEST_USER_ADMIN_PASS):
        self._logged_username = username
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': username,
                                  'password': password})

        if 'invalid user name' in response.body:
            self.fail('could not login using %s %s' % (username, password))

        self.assertEqual(response.status, '302 Found')
        ses = response.session['rhodecode_user']
        self.assertEqual(ses.get('username'), username)
        response = response.follow()
        self.assertEqual(ses.get('is_authenticated'), True)

        return response.session['rhodecode_user']

    def _get_logged_user(self):
        return User.get_by_username(self._logged_username)

    def checkSessionFlash(self, response, msg):
        self.assertTrue('flash' in response.session,
                        msg='Response session:%r have no flash'
                        % response.session)
        if not msg in response.session['flash'][0][1]:
            msg = u'msg `%s` not found in session flash: got `%s` instead' % (
                      msg, response.session['flash'][0][1])
            self.fail(safe_str(msg))
