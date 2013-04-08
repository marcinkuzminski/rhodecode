import os
import unittest
import functools
from rhodecode.tests import *

from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.db import RepoGroup

from rhodecode.model.meta import Session
from nose.tools import with_setup
from rhodecode.tests.models.common import _create_project_tree, check_tree_perms, \
    _get_perms, _check_expected_count, expected_count, _destroy_project_tree
from rhodecode.model.users_group import UserGroupModel
from rhodecode.tests.fixture import Fixture

fixture = Fixture()

test_u2_id = None
test_u2_gr_id = None
_get_repo_perms = None
_get_group_perms = None


def permissions_setup_func(group_name='g0', perm='group.read', recursive=True):
    """
    Resets all permissions to perm attribute
    """
    repos_group = RepoGroup.get_by_group_name(group_name=group_name)
    if not repos_group:
        raise Exception('Cannot get group %s' % group_name)
    perms_updates = [[test_u2_gr_id, perm, 'users_group']]
    ReposGroupModel()._update_permissions(repos_group,
                                          perms_updates=perms_updates,
                                          recursive=recursive)
    Session().commit()


def setup_module():
    global test_u2_id, test_u2_gr_id, _get_repo_perms, _get_group_perms
    test_u2 = _create_project_tree()
    Session().commit()
    test_u2_id = test_u2.user_id

    gr1 = fixture.create_user_group('perms_group_1')
    Session().commit()
    test_u2_gr_id = gr1.users_group_id
    UserGroupModel().add_user_to_group(gr1, user=test_u2_id)
    Session().commit()

    _get_repo_perms = functools.partial(_get_perms, key='repositories',
                                        test_u1_id=test_u2_id)
    _get_group_perms = functools.partial(_get_perms, key='repositories_groups',
                                         test_u1_id=test_u2_id)


def teardown_module():
    _destroy_project_tree(test_u2_id)


@with_setup(permissions_setup_func)
def test_user_permissions_on_group_without_recursive_mode():
    # set permission to g0 non-recursive mode
    recursive = False
    group = 'g0'
    permissions_setup_func(group, 'group.write', recursive=recursive)

    items = [x for x in _get_repo_perms(group, recursive)]
    expected = 0
    assert len(items) == expected, ' %s != %s' % (len(items), expected)
    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'repository.read'

    items = [x for x in _get_group_perms(group, recursive)]
    expected = 1
    assert len(items) == expected, ' %s != %s' % (len(items), expected)
    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'group.write'


@with_setup(permissions_setup_func)
def test_user_permissions_on_group_without_recursive_mode_subgroup():
    # set permission to g0 non-recursive mode
    recursive = False
    group = 'g0/g0_1'
    permissions_setup_func(group, 'group.write', recursive=recursive)

    items = [x for x in _get_repo_perms(group, recursive)]
    expected = 0
    assert len(items) == expected, ' %s != %s' % (len(items), expected)
    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'repository.read'

    items = [x for x in _get_group_perms(group, recursive)]
    expected = 1
    assert len(items) == expected, ' %s != %s' % (len(items), expected)
    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'group.write'


@with_setup(permissions_setup_func)
def test_user_permissions_on_group_with_recursive_mode():

    # set permission to g0 recursive mode, all children including
    # other repos and groups should have this permission now set !
    recursive = True
    group = 'g0'
    permissions_setup_func(group, 'group.write', recursive=recursive)

    repo_items = [x for x in _get_repo_perms(group, recursive)]
    items = [x for x in _get_group_perms(group, recursive)]
    _check_expected_count(items, repo_items, expected_count(group, True))

    for name, perm in repo_items:
        yield check_tree_perms, name, perm, group, 'repository.write'

    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'group.write'


@with_setup(permissions_setup_func)
def test_user_permissions_on_group_with_recursive_mode_inner_group():
    ## set permission to g0_3 group to none
    recursive = True
    group = 'g0/g0_3'
    permissions_setup_func(group, 'group.none', recursive=recursive)

    repo_items = [x for x in _get_repo_perms(group, recursive)]
    items = [x for x in _get_group_perms(group, recursive)]
    _check_expected_count(items, repo_items, expected_count(group, True))

    for name, perm in repo_items:
        yield check_tree_perms, name, perm, group, 'repository.none'

    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'group.none'


@with_setup(permissions_setup_func)
def test_user_permissions_on_group_with_recursive_mode_deepest():
    ## set permission to g0_3 group to none
    recursive = True
    group = 'g0/g0_1/g0_1_1'
    permissions_setup_func(group, 'group.write', recursive=recursive)

    repo_items = [x for x in _get_repo_perms(group, recursive)]
    items = [x for x in _get_group_perms(group, recursive)]
    _check_expected_count(items, repo_items, expected_count(group, True))

    for name, perm in repo_items:
        yield check_tree_perms, name, perm, group, 'repository.write'

    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'group.write'


@with_setup(permissions_setup_func)
def test_user_permissions_on_group_with_recursive_mode_only_with_repos():
    ## set permission to g0_3 group to none
    recursive = True
    group = 'g0/g0_2'
    permissions_setup_func(group, 'group.admin', recursive=recursive)

    repo_items = [x for x in _get_repo_perms(group, recursive)]
    items = [x for x in _get_group_perms(group, recursive)]
    _check_expected_count(items, repo_items, expected_count(group, True))

    for name, perm in repo_items:
        yield check_tree_perms, name, perm, group, 'repository.admin'

    for name, perm in items:
        yield check_tree_perms, name, perm, group, 'group.admin'
