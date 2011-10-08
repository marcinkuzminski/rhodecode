# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_hg_operations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test suite for making push/pull operations

    :created_on: Dec 30, 2010
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>
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
import sys
import shutil
import logging
from os.path import join as jn
from os.path import dirname as dn

from tempfile import _RandomNameSequence
from subprocess import Popen, PIPE

from paste.deploy import appconfig
from pylons import config
from sqlalchemy import engine_from_config

from rhodecode.lib.utils import add_cache
from rhodecode.model import init_model
from rhodecode.model import meta
from rhodecode.model.db import User, Repository
from rhodecode.lib.auth import get_crypt_password

from rhodecode.tests import TESTS_TMP_PATH, NEW_HG_REPO, HG_REPO
from rhodecode.config.environment import load_environment

rel_path = dn(dn(dn(os.path.abspath(__file__))))
conf = appconfig('config:development.ini', relative_to=rel_path)
load_environment(conf.global_conf, conf.local_conf)

add_cache(conf)

USER = 'test_admin'
PASS = 'test12'
HOST = '127.0.0.1:5000'
DEBUG = True
log = logging.getLogger(__name__)


class Command(object):

    def __init__(self, cwd):
        self.cwd = cwd

    def execute(self, cmd, *args):
        """Runs command on the system with given ``args``.
        """

        command = cmd + ' ' + ' '.join(args)
        log.debug('Executing %s' % command)
        if DEBUG:
            print command
        p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, cwd=self.cwd)
        stdout, stderr = p.communicate()
        if DEBUG:
            print stdout, stderr
        return stdout, stderr

def get_session():
    engine = engine_from_config(conf, 'sqlalchemy.db1.')
    init_model(engine)
    sa = meta.Session()
    return sa


def create_test_user(force=True):
    print 'creating test user'
    sa = get_session()

    user = sa.query(User).filter(User.username == USER).scalar()

    if force and user is not None:
        print 'removing current user'
        for repo in sa.query(Repository).filter(Repository.user == user).all():
            sa.delete(repo)
        sa.delete(user)
        sa.commit()

    if user is None or force:
        print 'creating new one'
        new_usr = User()
        new_usr.username = USER
        new_usr.password = get_crypt_password(PASS)
        new_usr.email = 'mail@mail.com'
        new_usr.name = 'test'
        new_usr.lastname = 'lasttestname'
        new_usr.active = True
        new_usr.admin = True
        sa.add(new_usr)
        sa.commit()

    print 'done'


def create_test_repo(force=True):
    print 'creating test repo'
    from rhodecode.model.repo import RepoModel
    sa = get_session()

    user = sa.query(User).filter(User.username == USER).scalar()
    if user is None:
        raise Exception('user not found')


    repo = sa.query(Repository).filter(Repository.repo_name == HG_REPO).scalar()

    if repo is None:
        print 'repo not found creating'

        form_data = {'repo_name':HG_REPO,
                     'repo_type':'hg',
                     'private':False,
                     'clone_uri':'' }
        rm = RepoModel(sa)
        rm.base_path = '/home/hg'
        rm.create(form_data, user)

    print 'done'

def set_anonymous_access(enable=True):
    sa = get_session()
    user = sa.query(User).filter(User.username == 'default').one()
    user.active = enable
    sa.add(user)
    sa.commit()

def get_anonymous_access():
    sa = get_session()
    return sa.query(User).filter(User.username == 'default').one().active


#==============================================================================
# TESTS
#==============================================================================
def test_clone_with_credentials(no_errors=False, repo=HG_REPO):
    cwd = path = jn(TESTS_TMP_PATH, repo)


    try:
        shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        #print 'made dirs %s' % jn(path)
    except OSError:
        raise


    clone_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s %(dest)s' % \
                  {'user':USER,
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':repo,
                   'dest':path + _RandomNameSequence().next()}

    stdout, stderr = Command(cwd).execute('hg clone', clone_url)

    if no_errors is False:
        assert """adding file changes""" in stdout, 'no messages about cloning'
        assert """abort""" not in stderr , 'got error from clone'

if __name__ == '__main__':
    try:
        create_test_user(force=False)

        for i in range(int(sys.argv[2])):
            test_clone_with_credentials(repo=sys.argv[1])

    except Exception, e:
        sys.exit('stop on %s' % e)
