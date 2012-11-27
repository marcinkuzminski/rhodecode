from __future__ import with_statement
import os
import unittest
from rhodecode.tests import *
from rhodecode.lib.diffs import DiffProcessor, NEW_FILENODE, DEL_FILENODE, \
    MOD_FILENODE, RENAMED_FILENODE, CHMOD_FILENODE

dn = os.path.dirname
FIXTURES = os.path.join(dn(dn(os.path.abspath(__file__))), 'fixtures')

DIFF_FIXTURES = {
    'hg_diff_add_single_binary_file.diff': [
        (u'US Warszawa.jpg', 'A', ['b', NEW_FILENODE]),
    ],
    'hg_diff_mod_single_binary_file.diff': [
        (u'US Warszawa.jpg', 'M', ['b', MOD_FILENODE]),
    ],
    'hg_diff_del_single_binary_file.diff': [
        (u'US Warszawa.jpg', 'D', ['b', DEL_FILENODE]),
    ],
    'hg_diff_binary_and_normal.diff': [
        (u'img/baseline-10px.png', 'A', ['b', NEW_FILENODE]),
        (u'js/jquery/hashgrid.js', 'A', [340, 0]),
        (u'index.html',            'M', [3, 2]),
        (u'less/docs.less',        'M', [34, 0]),
        (u'less/scaffolding.less', 'M', [1, 3]),
        (u'readme.markdown',       'M', [1, 10]),
        (u'img/baseline-20px.png', 'D', ['b', DEL_FILENODE]),
        (u'js/global.js',          'D', [0, 75])
    ],
    'hg_diff_chmod.diff': [
        (u'file', 'M', ['b', CHMOD_FILENODE]),
    ],
    'hg_diff_rename_file.diff': [
        (u'file_renamed', 'M', ['b', RENAMED_FILENODE]),
    ],
    'git_diff_chmod.diff': [
        (u'work-horus.xls', 'M', ['b', CHMOD_FILENODE]),
    ],
    'git_diff_rename_file.diff': [
        (u'file.xls', 'M', ['b', RENAMED_FILENODE]),
    ],
    'git_diff_mod_single_binary_file.diff': [
        ('US Warszawa.jpg', 'M', ['b', MOD_FILENODE])

    ],
    'git_diff_binary_and_normal.diff': [
        (u'img/baseline-10px.png', 'A', ['b', NEW_FILENODE]),
        (u'js/jquery/hashgrid.js', 'A', [340, 0]),
        (u'index.html',            'M', [3, 2]),
        (u'less/docs.less',        'M', [34, 0]),
        (u'less/scaffolding.less', 'M', [1, 3]),
        (u'readme.markdown',       'M', [1, 10]),
        (u'img/baseline-20px.png', 'D', ['b', DEL_FILENODE]),
        (u'js/global.js',          'D', [0, 75])
    ],
    'diff_with_diff_data.diff': [
        (u'vcs/backends/base.py', 'M', [18, 2]),
        (u'vcs/backends/git/repository.py', 'M', [46, 15]),
        (u'vcs/backends/hg.py', 'M', [22, 3]),
        (u'vcs/tests/test_git.py', 'M', [5, 5]),
        (u'vcs/tests/test_repository.py', 'M', [174, 2])
    ],
#    'large_diff.diff': [
#
#    ],


}


def _diff_checker(fixture):
    with open(os.path.join(FIXTURES, fixture)) as f:
        diff = f.read()

    diff_proc = DiffProcessor(diff)
    diff_proc_d = diff_proc.prepare()
    data = [(x['filename'], x['operation'], x['stats']) for x in diff_proc_d]
    expected_data = DIFF_FIXTURES[fixture]

    assert expected_data == data


def test_parse_diff():
    for fixture in DIFF_FIXTURES:
        yield _diff_checker, fixture
