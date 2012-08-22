# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_scm_operations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test suite for making push/pull operations.
    Run using::

     RC_WHOOSH_TEST_DISABLE=1 nosetests rhodecode/tests/scripts/test_scm_operations.py

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
from os.path import join as jn
from os.path import dirname as dn

from tempfile import _RandomNameSequence
from subprocess import Popen, PIPE

from rhodecode.tests import *
from rhodecode.model.db import User, Repository, UserLog
from rhodecode.model.meta import Session

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


def set_anonymous_access(enable=True):
    user = User.get_by_username(User.DEFAULT_USER)
    user.active = enable
    Session().add(user)
    Session().commit()
    print '\tanonymous access is now:', enable
    if enable != User.get_by_username(User.DEFAULT_USER).active:
        raise Exception('Cannot set anonymous access')


def setup_module():
    #DISABLE ANONYMOUS ACCESS
    set_anonymous_access(False)


def test_clone_hg_repo_by_admin():
    clone_url = _construct_url(HG_REPO)
    stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

    assert 'requesting all changes' in stdout
    assert 'adding changesets' in stdout
    assert 'adding manifests' in stdout
    assert 'adding file changes' in stdout

    assert stderr == ''


def test_clone_git_repo_by_admin():
    clone_url = _construct_url(GIT_REPO)
    stdout, stderr = Command('/tmp').execute('git clone', clone_url)

    assert 'Cloning into' in stdout
    assert stderr == ''


def test_clone_wrong_credentials_hg():
    clone_url = _construct_url(HG_REPO, passwd='bad!')
    stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
    assert 'abort: authorization failed' in stderr


def test_clone_wrong_credentials_git():
    clone_url = _construct_url(GIT_REPO, passwd='bad!')
    stdout, stderr = Command('/tmp').execute('git clone', clone_url)
    assert 'fatal: Authentication failed' in stderr


def test_clone_git_dir_as_hg():
    clone_url = _construct_url(GIT_REPO)
    stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
    assert 'HTTP Error 404: Not Found' in stderr


def test_clone_hg_repo_as_git():
    clone_url = _construct_url(HG_REPO)
    stdout, stderr = Command('/tmp').execute('git clone', clone_url)
    assert 'not found: did you run git update-server-info on the server' in stderr


def test_clone_non_existing_path_hg():
    clone_url = _construct_url('trololo')
    stdout, stderr = Command('/tmp').execute('hg clone', clone_url)
    assert 'HTTP Error 404: Not Found' in stderr


def test_clone_non_existing_path_git():
    clone_url = _construct_url('trololo')
    stdout, stderr = Command('/tmp').execute('git clone', clone_url)
    assert 'not found: did you run git update-server-info on the server' in stderr


def test_push_new_file_hg():
    DEST = _get_tmp_dir()
    clone_url = _construct_url(HG_REPO, dest=DEST)
    stdout, stderr = Command('/tmp').execute('hg clone', clone_url)

    # commit some stuff into this repo
    cwd = path = jn(DEST)
    added_file = jn(path, '%ssetupążźć.py' % _RandomNameSequence().next())
    Command(cwd).execute('touch %s' % added_file)
    Command(cwd).execute('hg add %s' % added_file)

    for i in xrange(3):
        cmd = """echo 'added_line%s' >> %s""" % (i, added_file)
        Command(cwd).execute(cmd)

        cmd = """hg ci -m 'commited new %s' -u '%s' %s """ % (
                i,
                'Marcin Kuźminski <marcin@python-blog.com>',
                added_file
        )
        Command(cwd).execute(cmd)
    # PUSH it back
    clone_url = _construct_url(HG_REPO, dest='')
    stdout, stderr = Command(cwd).execute('hg push --verbose', clone_url)

    assert 'pushing to' in stdout
    assert 'Repository size' in stdout
    assert 'Last revision is now' in stdout


def test_push_new_file_git():
    DEST = _get_tmp_dir()
    clone_url = _construct_url(GIT_REPO, dest=DEST)
    stdout, stderr = Command('/tmp').execute('git clone', clone_url)

    # commit some stuff into this repo
    cwd = path = jn(DEST)
    added_file = jn(path, '%ssetupążźć.py' % _RandomNameSequence().next())
    Command(cwd).execute('touch %s' % added_file)
    Command(cwd).execute('git add %s' % added_file)

    for i in xrange(3):
        cmd = """echo 'added_line%s' >> %s""" % (i, added_file)
        Command(cwd).execute(cmd)

        cmd = """git ci -m 'commited new %s' --author '%s' %s """ % (
                i,
                'Marcin Kuźminski <marcin@python-blog.com>',
                added_file
        )
        Command(cwd).execute(cmd)
    # PUSH it back
    clone_url = _construct_url(GIT_REPO, dest='')
    stdout, stderr = Command(cwd).execute('git push --verbose', clone_url)

    #WTF git stderr ?!
    assert 'master -> master' in stderr


def test_push_modify_existing_file_hg():
    assert 0


def test_push_modify_existing_file_git():
    assert 0


def test_push_wrong_credentials_hg():
    assert 0


def test_push_wrong_credentials_git():
    assert 0


def test_push_back_to_wrong_url_hg():
    assert 0


def test_push_back_to_wrong_url_git():
    assert 0


#TODO: write all locking tests
