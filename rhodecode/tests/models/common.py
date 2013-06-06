from rhodecode.tests import *
from rhodecode.tests.fixture import Fixture

from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import RepoGroup, Repository, User
from rhodecode.model.user import UserModel

from rhodecode.lib.auth import AuthUser
from rhodecode.model.meta import Session


fixture = Fixture()


def _destroy_project_tree(test_u1_id):
    Session.remove()
    repos_group = RepoGroup.get_by_group_name(group_name='g0')
    for el in reversed(repos_group.recursive_groups_and_repos()):
        if isinstance(el, Repository):
            RepoModel().delete(el)
        elif isinstance(el, RepoGroup):
            ReposGroupModel().delete(el, force_delete=True)

    u = User.get(test_u1_id)
    Session().delete(u)
    Session().commit()


def _create_project_tree():
    """
    Creates a tree of groups and repositories to test permissions

    structure
     [g0] - group `g0` with 3 subgroups
     |
     |__[g0_1] group g0_1 with 2 groups 0 repos
     |  |
     |  |__[g0_1_1] group g0_1_1 with 1 group 2 repos
     |  |   |__<g0/g0_1/g0_1_1/g0_1_1_r1>
     |  |   |__<g0/g0_1/g0_1_1/g0_1_1_r2>
     |  |__<g0/g0_1/g0_1_r1>
     |
     |__[g0_2] 2 repos
     |  |
     |  |__<g0/g0_2/g0_2_r1>
     |  |__<g0/g0_2/g0_2_r2>
     |
     |__[g0_3] 1 repo
        |
        |_<g0/g0_3/g0_3_r1>
        |_<g0/g0_3/g0_3_r2_private>

    """
    test_u1 = UserModel().create_or_update(
        username=u'test_u1', password=u'qweqwe',
        email=u'test_u1@rhodecode.org', firstname=u'test_u1', lastname=u'test_u1'
    )
    g0 = fixture.create_group('g0')
    g0_1 = fixture.create_group('g0_1', group_parent_id=g0)
    g0_1_1 = fixture.create_group('g0_1_1', group_parent_id=g0_1)
    g0_1_1_r1 = fixture.create_repo('g0/g0_1/g0_1_1/g0_1_1_r1', repos_group=g0_1_1)
    g0_1_1_r2 = fixture.create_repo('g0/g0_1/g0_1_1/g0_1_1_r2', repos_group=g0_1_1)
    g0_1_r1 = fixture.create_repo('g0/g0_1/g0_1_r1', repos_group=g0_1)
    g0_2 = fixture.create_group('g0_2', group_parent_id=g0)
    g0_2_r1 = fixture.create_repo('g0/g0_2/g0_2_r1', repos_group=g0_2)
    g0_2_r2 = fixture.create_repo('g0/g0_2/g0_2_r2', repos_group=g0_2)
    g0_3 = fixture.create_group('g0_3', group_parent_id=g0)
    g0_3_r1 = fixture.create_repo('g0/g0_3/g0_3_r1', repos_group=g0_3)
    g0_3_r2_private = fixture.create_repo('g0/g0_3/g0_3_r1_private',
                                          repos_group=g0_3, repo_private=True)
    return test_u1


def expected_count(group_name, objects=False):
    repos_group = RepoGroup.get_by_group_name(group_name=group_name)
    objs = repos_group.recursive_groups_and_repos()
    if objects:
        return objs
    return len(objs)


def _check_expected_count(items, repo_items, expected):
    should_be = len(items + repo_items)
    there_are = len(expected)
    assert  should_be == there_are, ('%s != %s' % ((items + repo_items), expected))


def check_tree_perms(obj_name, repo_perm, prefix, expected_perm):
    assert repo_perm == expected_perm, ('obj:`%s` got perm:`%s` should:`%s`'
                                    % (obj_name, repo_perm, expected_perm))


def _get_perms(filter_='', recursive=True, key=None, test_u1_id=None):
    test_u1 = AuthUser(user_id=test_u1_id)
    for k, v in test_u1.permissions[key].items():
        if recursive and k.startswith(filter_):
            yield k, v
        elif not recursive:
            if k == filter_:
                yield k, v
