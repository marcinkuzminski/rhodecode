# -*- coding: utf-8 -*-
"""
    rhodecode.tests.test_hg_operations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test suite for making push/pull operations
    
    :created_on: Dec 30, 2010
    :copyright: (c) 2010 by marcink.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""

import os
import shutil
import logging

from subprocess import Popen, PIPE

from os.path import join as jn

from rhodecode.tests import TESTS_TMP_PATH, NEW_HG_REPO, HG_REPO

USER = 'test_admin'
PASS = 'test12'
HOST = '127.0.0.1:5000'

log = logging.getLogger(__name__)

def __execute_cmd(cmd, *args):
    """Runs command on the system with given ``args``.
    """

    command = cmd + ' ' + ' '.join(args)
    log.debug('Executing %s' % command)
    print command
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    print stdout, stderr
    return stdout, stderr


#===============================================================================
# TESTS
#===============================================================================
def test_clone():
    #rm leftovers
    try:
        log.debug('removing old directory')
        shutil.rmtree(jn(TESTS_TMP_PATH, HG_REPO))
    except OSError:
        pass

    clone_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s %(dest)s' % \
                  {'user':USER,
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO,
                   'dest':jn(TESTS_TMP_PATH, HG_REPO)}

    stdout, stderr = __execute_cmd('hg clone', clone_url)

def test_pull():
    pass

def test_push():

    modified_file = jn(TESTS_TMP_PATH, HG_REPO, 'setup.py')
    for i in xrange(5):
        cmd = """echo 'added_line%s' >> %s""" % (i, modified_file)
        __execute_cmd(cmd)

        cmd = """hg ci -m 'changed file %s' %s """ % (i, modified_file)
        __execute_cmd(cmd)

    __execute_cmd('hg push %s' % jn(TESTS_TMP_PATH, HG_REPO))

def test_push_new_file():
    added_file = jn(TESTS_TMP_PATH, HG_REPO, 'setup.py')

    __execute_cmd('touch %s' % added_file)

    __execute_cmd('hg add %s' % added_file)

    for i in xrange(15):
        cmd = """echo 'added_line%s' >> %s""" % (i, added_file)
        __execute_cmd(cmd)

        cmd = """hg ci -m 'commited new %s' %s """ % (i, added_file)
        __execute_cmd(cmd)

    __execute_cmd('hg push %s' % jn(TESTS_TMP_PATH, HG_REPO))

def test_push_wrong_credentials():

    clone_url = 'http://%(user)s:%(pass)s@%(host)s/%(cloned_repo)s' % \
                  {'user':USER + 'xxx',
                   'pass':PASS,
                   'host':HOST,
                   'cloned_repo':HG_REPO,
                   'dest':jn(TESTS_TMP_PATH, HG_REPO)}

    modified_file = jn(TESTS_TMP_PATH, HG_REPO, 'setup.py')
    for i in xrange(5):
        cmd = """echo 'added_line%s' >> %s""" % (i, modified_file)
        __execute_cmd(cmd)

        cmd = """hg ci -m 'commited %s' %s """ % (i, modified_file)
        __execute_cmd(cmd)

    __execute_cmd('hg push %s' % clone_url)

def test_push_wrong_path():
    added_file = jn(TESTS_TMP_PATH, HG_REPO, 'somefile.py')

    try:
        os.makedirs(jn(TESTS_TMP_PATH, HG_REPO))
    except OSError:
        pass

    __execute_cmd("""echo '' > %s""" % added_file)

    __execute_cmd("""hg add %s""" % added_file)

    for i in xrange(2):
        cmd = """echo 'added_line%s' >> %s""" % (i, added_file)
        __execute_cmd(cmd)

        cmd = """hg ci -m 'commited new %s' %s """ % (i, added_file)
        __execute_cmd(cmd)

    __execute_cmd('hg push %s' % jn(TESTS_TMP_PATH, HG_REPO + '_error'))

if __name__ == '__main__':
    test_clone()
    test_push_wrong_path()
    test_push_wrong_credentials()
    test_push_new_file()

