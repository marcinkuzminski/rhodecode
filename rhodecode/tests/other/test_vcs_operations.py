# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_scm_operations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test suite for making push/pull operations.
    Run using after doing paster serve test.ini::
     RC_WHOOSH_TEST_DISABLE=1 RC_NO_TMP_PATH=1 nosetests rhodecode/tests/scripts/test_vcs_operations.py

    You must have git > 1.8.1 for tests to work fine

    :created_on: Dec 30, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import tempfile
import unittest
import time
from os.path import join as jn
from os.path import dirname as dn

from tempfile import _RandomNameSequence
from subprocess import Popen, PIPE

from rhodecode.tests import *
from rhodecode.model.db import User, Repository, UserLog, UserIpMap,\
    CacheInvalidation
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel

DEBUG = True
HOST = '127.0.0.1:5000'  # test host


class Command(object):

    def __init__(self, cwd):
        self.cwd = cwd

    def execute(self, cmd, *args):
        """
        Runs command on the system with given ``args``.
        """

        command = cmd + ' ' + ' '.join(args)
        if DEBUG:
            print '*** CMD %s ***' % command
        p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, cwd=self.cwd)
        stdout, stderr = p.communicate()
        if DEBUG:
            print stdout, stderr
        return stdout, stderr


def _get_tmp_dir():
    return tempfile.mkdtemp(prefix='rc_integration_test')


def _construct_url(repo, dest=None, **kwargs):
    if dest is None:
        #make temp clone
        dest = _get_tmp_dir()
    params = {
        'user': TEST_USER_ADMIN_LOGIN,
        'passwd': TEST_USER_ADMIN_PASS,
        'host': HOST,
        'cloned_repo': repo,
        'dest': dest
    }
    params.update(**kwargs)
    if params['user'] and params['passwd']:
        _url = 'http://%(user)s:%(passwd)s@%(host)s/%(cloned_repo)s %(dest)s' % params
    else:
        _url = 'http://(host)s/%(cloned_repo)s %(dest)s' % params
    return _url


def _add_files_and_push(vcs, DEST, **kwargs):
    """
    Generate some files, add it to DEST repo and push back
    vcs is git or hg and defines what VCS we want to make those files for

    :param vcs:
    :param DEST:
    """
    # commit some stuff into this repo
    cwd = path = jn(DEST)
    #added_file = jn(path, '%ssetupążźć.py' % _RandomNameSequence().next())
    added_file = jn(path, '%ssetup.py' % _RandomNameSequence().next())
    Command(cwd).execute('touch %s' % added_file)
    Command(cwd).execute('%s add %s' % (vcs, added_file))

    for i in xrange(kwargs.get('files_no', 3)):
        cmd = """echo 'added_line%s' >> %s""" % (i, added_file)
        Command(cwd).execute(cmd)
        author_str = 'Marcin Kuźminski <me@email.com>'
        if vcs == 'hg':
            cmd = """hg commit -m 'commited new %s' -u '%s' %s """ % (
                i, author_str, added_file
            )
        elif vcs == 'git':
            cmd = """git commit -m 'commited new %s' --author '%s' %s """ % (
                i, author_str, added_file
            )
        Command(cwd).execute(cmd)
    # PUSH it back
    if vcs == 'hg':
        _REPO = HG_REPO
    elif vcs == 'git':
        _REPO = GIT_REPO

    kwargs['dest'] = ''
    clone_url = _construct_url(_REPO, **kwargs)
    if 'clone_url' in kwargs:
        clone_url = kwargs['clone_url']
    if vcs == 'hg':
        stdout, stderr = Command(cwd).execute('hg push --verbose', clone_url)
    elif vcs == 'git':
        stdout, stderr = Command(cwd).execute('git push --verbose', clone_url + " master")

    return stdout, stderr


def set_anonymous_access(enable=True):
    user = User.get_by_username(User.DEFAULT_USER)
    user.active = enable
    Session().add(user)
    Session().commit()
    print '\tanonymous access is now:', enable
    if enable != User.get_by_username(User.DEFAULT_USER).active:
        raise Exception('Cannot set anonymous access')


#==============================================================================
# TESTS
#==============================================================================

class TestVCSOperations(BaseTestCase):

    @classmethod
    def setup_class(cls):
        #DISABLE ANONYMOUS ACCESS
        set_anonymous_access(False)

    def setUp(self):
        r = Repository.get_by_repo_name(GIT_REPO)
        Repository.unlock(r)
        r.enable_locking = False
        Session().add(r)
        Session().commit()

        r = Repository.get_by_repo_name(HG_REPO)
        Repository.unlock(r)
        r.enable_locking = False
        Session().add(r)
        Session().commit()

    def test_clone_hg_repo_by_admin(self):
        clone_url = _construct_url(HG_REPO)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        assert 'requesting all changes' in stdout
        assert 'adding changesets' in stdout
        assert 'adding manifests' in stdout
        assert 'adding file changes' in stdout

        assert stderr == ''

    def test_clone_git_repo_by_admin(self):
        clone_url = _construct_url(GIT_REPO)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)

        assert 'Cloning into' in stdout
        assert stderr == ''

    def test_clone_wrong_credentials_hg(self):
        clone_url = _construct_url(HG_REPO, passwd='bad!')
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
        assert 'abort: authorization failed' in stderr

    def test_clone_wrong_credentials_git(self):
        clone_url = _construct_url(GIT_REPO, passwd='bad!')
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)
        assert 'fatal: Authentication failed' in stderr

    def test_clone_git_dir_as_hg(self):
        clone_url = _construct_url(GIT_REPO)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
        assert 'HTTP Error 404: Not Found' in stderr

    def test_clone_hg_repo_as_git(self):
        clone_url = _construct_url(HG_REPO)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)
        assert 'not found:' in stderr

    def test_clone_non_existing_path_hg(self):
        clone_url = _construct_url('trololo')
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
        assert 'HTTP Error 404: Not Found' in stderr

    def test_clone_non_existing_path_git(self):
        clone_url = _construct_url('trololo')
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)
        assert 'not found:' in stderr

    def test_push_new_file_hg(self):
        DEST = _get_tmp_dir()
        clone_url = _construct_url(HG_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        stdout, stderr = _add_files_and_push('hg', DEST)

        assert 'pushing to' in stdout
        assert 'Repository size' in stdout
        assert 'Last revision is now' in stdout

    def test_push_new_file_git(self):
        DEST = _get_tmp_dir()
        clone_url = _construct_url(GIT_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)

        # commit some stuff into this repo
        stdout, stderr = _add_files_and_push('git', DEST)

        #WTF git stderr ?!
        assert 'master -> master' in stderr

    def test_push_invalidates_cache_hg(self):
        key = CacheInvalidation.query().filter(CacheInvalidation.cache_key
                                               ==HG_REPO).one()
        key.cache_active = True
        Session().add(key)
        Session().commit()

        DEST = _get_tmp_dir()
        clone_url = _construct_url(HG_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        stdout, stderr = _add_files_and_push('hg', DEST, files_no=1)
        key = CacheInvalidation.query().filter(CacheInvalidation.cache_key
                                               ==HG_REPO).one()
        self.assertEqual(key.cache_active, False)

    def test_push_invalidates_cache_git(self):
        key = CacheInvalidation.query().filter(CacheInvalidation.cache_key
                                               ==GIT_REPO).one()
        key.cache_active = True
        Session().add(key)
        Session().commit()

        DEST = _get_tmp_dir()
        clone_url = _construct_url(GIT_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)

        # commit some stuff into this repo
        stdout, stderr = _add_files_and_push('git', DEST, files_no=1)

        key = CacheInvalidation.query().filter(CacheInvalidation.cache_key
                                               ==GIT_REPO).one()
        self.assertEqual(key.cache_active, False)

    def test_push_wrong_credentials_hg(self):
        DEST = _get_tmp_dir()
        clone_url = _construct_url(HG_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        stdout, stderr = _add_files_and_push('hg', DEST, user='bad',
                                             passwd='name')

        assert 'abort: authorization failed' in stderr

    def test_push_wrong_credentials_git(self):
        DEST = _get_tmp_dir()
        clone_url = _construct_url(GIT_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)

        stdout, stderr = _add_files_and_push('git', DEST, user='bad',
                                             passwd='name')

        assert 'fatal: Authentication failed' in stderr

    def test_push_back_to_wrong_url_hg(self):
        DEST = _get_tmp_dir()
        clone_url = _construct_url(HG_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        stdout, stderr = _add_files_and_push('hg', DEST,
                                    clone_url='http://127.0.0.1:5000/tmp',)

        assert 'HTTP Error 404: Not Found' in stderr

    def test_push_back_to_wrong_url_git(self):
        DEST = _get_tmp_dir()
        clone_url = _construct_url(GIT_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)

        stdout, stderr = _add_files_and_push('git', DEST,
                                    clone_url='http://127.0.0.1:5000/tmp',)

        assert 'not found:' in stderr

    def test_clone_and_create_lock_hg(self):
        # enable locking
        r = Repository.get_by_repo_name(HG_REPO)
        r.enable_locking = True
        Session().add(r)
        Session().commit()
        # clone
        clone_url = _construct_url(HG_REPO)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        #check if lock was made
        r = Repository.get_by_repo_name(HG_REPO)
        assert r.locked[0] == User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id

    def test_clone_and_create_lock_git(self):
        # enable locking
        r = Repository.get_by_repo_name(GIT_REPO)
        r.enable_locking = True
        Session().add(r)
        Session().commit()
        # clone
        clone_url = _construct_url(GIT_REPO)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)

        #check if lock was made
        r = Repository.get_by_repo_name(GIT_REPO)
        assert r.locked[0] == User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id

    def test_clone_after_repo_was_locked_hg(self):
        #lock repo
        r = Repository.get_by_repo_name(HG_REPO)
        Repository.lock(r, User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id)
        #pull fails since repo is locked
        clone_url = _construct_url(HG_REPO)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
        msg = ("""abort: HTTP Error 423: Repository `%s` locked by user `%s`"""
                % (HG_REPO, TEST_USER_ADMIN_LOGIN))
        assert msg in stderr

    def test_clone_after_repo_was_locked_git(self):
        #lock repo
        r = Repository.get_by_repo_name(GIT_REPO)
        Repository.lock(r, User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id)
        #pull fails since repo is locked
        clone_url = _construct_url(GIT_REPO)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)
        msg = ("""The requested URL returned error: 423""")
        assert msg in stderr

    def test_push_on_locked_repo_by_other_user_hg(self):
        #clone some temp
        DEST = _get_tmp_dir()
        clone_url = _construct_url(HG_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        #lock repo
        r = Repository.get_by_repo_name(HG_REPO)
        # let this user actually push !
        RepoModel().grant_user_permission(repo=r, user=TEST_USER_REGULAR_LOGIN,
                                          perm='repository.write')
        Session().commit()
        Repository.lock(r, User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id)

        #push fails repo is locked by other user !
        stdout, stderr = _add_files_and_push('hg', DEST,
                                             user=TEST_USER_REGULAR_LOGIN,
                                             passwd=TEST_USER_REGULAR_PASS)
        msg = ("""abort: HTTP Error 423: Repository `%s` locked by user `%s`"""
                % (HG_REPO, TEST_USER_ADMIN_LOGIN))
        assert msg in stderr

#TODO: fix me ! somehow during tests hooks don't get called on GIT
#    def test_push_on_locked_repo_by_other_user_git(self):
#        #clone some temp
#        DEST = _get_tmp_dir()
#        clone_url = _construct_url(GIT_REPO, dest=DEST)
#        stdout, stderr = Command('/tmp').execute('git clone', clone_url)
#
#        #lock repo
#        r = Repository.get_by_repo_name(GIT_REPO)
#        # let this user actually push !
#        RepoModel().grant_user_permission(repo=r, user=TEST_USER_REGULAR_LOGIN,
#                                          perm='repository.write')
#        Session().commit()
#        Repository.lock(r, User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id)
#
#        #push fails repo is locked by other user !
#        stdout, stderr = _add_files_and_push('git', DEST,
#                                             user=TEST_USER_REGULAR_LOGIN,
#                                             passwd=TEST_USER_REGULAR_PASS)
#        msg = ("""abort: HTTP Error 423: Repository `%s` locked by user `%s`"""
#                % (GIT_REPO, TEST_USER_ADMIN_LOGIN))
#        #TODO: fix this somehow later on GIT, GIT is stupid and even if we throw
#        # back 423 to it, it makes ANOTHER request and we fail there with 405 :/
#        msg = "405 Method Not Allowed"
#        assert msg in stderr

    def test_push_unlocks_repository_hg(self):
        # enable locking
        r = Repository.get_by_repo_name(HG_REPO)
        r.enable_locking = True
        Session().add(r)
        Session().commit()
        #clone some temp
        DEST = _get_tmp_dir()
        clone_url = _construct_url(HG_REPO, dest=DEST)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        #check for lock repo after clone
        r = Repository.get_by_repo_name(HG_REPO)
        assert r.locked[0] == User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id

        #push is ok and repo is now unlocked
        stdout, stderr = _add_files_and_push('hg', DEST)
        assert ('remote: Released lock on repo `%s`' % HG_REPO) in stdout
        #we need to cleanup the Session Here !
        Session.remove()
        r = Repository.get_by_repo_name(HG_REPO)
        assert r.locked == [None, None]

#TODO: fix me ! somehow during tests hooks don't get called on GIT
#    def test_push_unlocks_repository_git(self):
#        # enable locking
#        r = Repository.get_by_repo_name(GIT_REPO)
#        r.enable_locking = True
#        Session().add(r)
#        Session().commit()
#        #clone some temp
#        DEST = _get_tmp_dir()
#        clone_url = _construct_url(GIT_REPO, dest=DEST)
#        stdout, stderr = Command('/tmp').execute('git clone', clone_url)
#
#        #check for lock repo after clone
#        r = Repository.get_by_repo_name(GIT_REPO)
#        assert r.locked[0] == User.get_by_username(TEST_USER_ADMIN_LOGIN).user_id
#
#        #push is ok and repo is now unlocked
#        stdout, stderr = _add_files_and_push('git', DEST)
#        #assert ('remote: Released lock on repo `%s`' % GIT_REPO) in stdout
#        #we need to cleanup the Session Here !
#        Session.remove()
#        r = Repository.get_by_repo_name(GIT_REPO)
#        assert r.locked == [None, None]

    def test_ip_restriction_hg(self):
        user_model = UserModel()
        try:
            user_model.add_extra_ip(TEST_USER_ADMIN_LOGIN, '10.10.10.10/32')
            Session().commit()
            clone_url = _construct_url(HG_REPO)
            stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
            assert 'abort: HTTP Error 403: Forbidden' in stderr
        finally:
            #release IP restrictions
            for ip in UserIpMap.getAll():
                UserIpMap.delete(ip.ip_id)
            Session().commit()

        time.sleep(2)
        clone_url = _construct_url(HG_REPO)
        stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

        assert 'requesting all changes' in stdout
        assert 'adding changesets' in stdout
        assert 'adding manifests' in stdout
        assert 'adding file changes' in stdout

        assert stderr == ''

    def test_ip_restriction_git(self):
        user_model = UserModel()
        try:
            user_model.add_extra_ip(TEST_USER_ADMIN_LOGIN, '10.10.10.10/32')
            Session().commit()
            clone_url = _construct_url(GIT_REPO)
            stdout, stderr = Command('/tmp').execute('git clone', clone_url)
            msg = ("""The requested URL returned error: 403""")
            assert msg in stderr
        finally:
            #release IP restrictions
            for ip in UserIpMap.getAll():
                UserIpMap.delete(ip.ip_id)
            Session().commit()

        time.sleep(2)
        clone_url = _construct_url(GIT_REPO)
        stdout, stderr = Command('/tmp').execute('git clone', clone_url)

        assert 'Cloning into' in stdout
        assert stderr == ''
