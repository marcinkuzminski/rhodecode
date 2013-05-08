import os
from sqlalchemy.exc import IntegrityError

from rhodecode.tests import *
from rhodecode.tests.fixture import Fixture

from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import RepoGroup
from rhodecode.model.meta import Session


fixture = Fixture()


def _update_group(id_, group_name, desc='desc', parent_id=None):
    form_data = fixture._get_group_create_params(group_name=group_name,
                                                 group_desc=desc,
                                                 group_parent_id=parent_id)
    gr = ReposGroupModel().update(id_, form_data)
    return gr


def _update_repo(name, **kwargs):
    form_data = fixture._get_repo_create_params(**kwargs)
    if not 'repo_name' in kwargs:
        form_data['repo_name'] = name
    if not 'perms_new' in kwargs:
        form_data['perms_new'] = []
    if not 'perms_updates' in kwargs:
        form_data['perms_updates'] = []
    r = RepoModel().update(name, **form_data)
    return r


class TestReposGroups(BaseTestCase):

    def setUp(self):
        self.g1 = fixture.create_group('test1', skip_if_exists=True)
        self.g2 = fixture.create_group('test2', skip_if_exists=True)
        self.g3 = fixture.create_group('test3', skip_if_exists=True)

    def tearDown(self):
        Session.remove()

    def __check_path(self, *path):
        """
        Checks the path for existance !
        """
        path = [TESTS_TMP_PATH] + list(path)
        path = os.path.join(*path)
        return os.path.isdir(path)

    def _check_folders(self):
        print os.listdir(TESTS_TMP_PATH)

    def __delete_group(self, id_):
        ReposGroupModel().delete(id_)

    def test_create_group(self):
        g = fixture.create_group('newGroup')
        Session().commit()
        self.assertEqual(g.full_path, 'newGroup')

        self.assertTrue(self.__check_path('newGroup'))

    def test_create_same_name_group(self):
        self.assertRaises(IntegrityError, lambda: fixture.create_group('newGroup'))
        Session().rollback()

    def test_same_subgroup(self):
        sg1 = fixture.create_group('sub1', group_parent_id=self.g1.group_id)
        self.assertEqual(sg1.parent_group, self.g1)
        self.assertEqual(sg1.full_path, 'test1/sub1')
        self.assertTrue(self.__check_path('test1', 'sub1'))

        ssg1 = fixture.create_group('subsub1', group_parent_id=sg1.group_id)
        self.assertEqual(ssg1.parent_group, sg1)
        self.assertEqual(ssg1.full_path, 'test1/sub1/subsub1')
        self.assertTrue(self.__check_path('test1', 'sub1', 'subsub1'))

    def test_remove_group(self):
        sg1 = fixture.create_group('deleteme')
        self.__delete_group(sg1.group_id)

        self.assertEqual(RepoGroup.get(sg1.group_id), None)
        self.assertFalse(self.__check_path('deteteme'))

        sg1 = fixture.create_group('deleteme', group_parent_id=self.g1.group_id)
        self.__delete_group(sg1.group_id)

        self.assertEqual(RepoGroup.get(sg1.group_id), None)
        self.assertFalse(self.__check_path('test1', 'deteteme'))

    def test_rename_single_group(self):
        sg1 = fixture.create_group('initial')

        new_sg1 = _update_group(sg1.group_id, 'after')
        self.assertTrue(self.__check_path('after'))
        self.assertEqual(RepoGroup.get_by_group_name('initial'), None)

    def test_update_group_parent(self):

        sg1 = fixture.create_group('initial', group_parent_id=self.g1.group_id)

        new_sg1 = _update_group(sg1.group_id, 'after', parent_id=self.g1.group_id)
        self.assertTrue(self.__check_path('test1', 'after'))
        self.assertEqual(RepoGroup.get_by_group_name('test1/initial'), None)

        new_sg1 = _update_group(sg1.group_id, 'after', parent_id=self.g3.group_id)
        self.assertTrue(self.__check_path('test3', 'after'))
        self.assertEqual(RepoGroup.get_by_group_name('test3/initial'), None)

        new_sg1 = _update_group(sg1.group_id, 'hello')
        self.assertTrue(self.__check_path('hello'))

        self.assertEqual(RepoGroup.get_by_group_name('hello'), new_sg1)

    def test_subgrouping_with_repo(self):

        g1 = fixture.create_group('g1')
        g2 = fixture.create_group('g2')
        # create new repo
        r = fixture.create_repo('john')

        self.assertEqual(r.repo_name, 'john')
        # put repo into group
        r = _update_repo('john', repo_group=g1.group_id)
        Session().commit()
        self.assertEqual(r.repo_name, 'g1/john')

        _update_group(g1.group_id, 'g1', parent_id=g2.group_id)
        self.assertTrue(self.__check_path('g2', 'g1'))

        # test repo
        self.assertEqual(r.repo_name, RepoGroup.url_sep().join(['g2', 'g1',
                                                                r.just_name]))

    def test_move_to_root(self):
        g1 = fixture.create_group('t11')
        g2 = fixture.create_group('t22', group_parent_id=g1.group_id)

        self.assertEqual(g2.full_path, 't11/t22')
        self.assertTrue(self.__check_path('t11', 't22'))

        g2 = _update_group(g2.group_id, 'g22', parent_id=None)
        Session().commit()

        self.assertEqual(g2.group_name, 'g22')
        # we moved out group from t1 to '' so it's full path should be 'g2'
        self.assertEqual(g2.full_path, 'g22')
        self.assertFalse(self.__check_path('t11', 't22'))
        self.assertTrue(self.__check_path('g22'))

    def test_rename_top_level_group_in_nested_setup(self):
        g1 = fixture.create_group('L1')
        g2 = fixture.create_group('L2', group_parent_id=g1.group_id)
        g3 = fixture.create_group('L3', group_parent_id=g2.group_id)

        r = fixture.create_repo('L1/L2/L3/L3_REPO', repo_group=g3.group_id)

        ##rename L1 all groups should be now changed
        _update_group(g1.group_id, 'L1_NEW')
        Session().commit()
        self.assertEqual(g1.full_path, 'L1_NEW')
        self.assertEqual(g2.full_path, 'L1_NEW/L2')
        self.assertEqual(g3.full_path, 'L1_NEW/L2/L3')
        self.assertEqual(r.repo_name,  'L1_NEW/L2/L3/L3_REPO')

    def test_change_parent_of_top_level_group_in_nested_setup(self):
        g1 = fixture.create_group('R1')
        g2 = fixture.create_group('R2', group_parent_id=g1.group_id)
        g3 = fixture.create_group('R3', group_parent_id=g2.group_id)
        g4 = fixture.create_group('R1_NEW')

        r = fixture.create_repo('R1/R2/R3/R3_REPO', repo_group=g3.group_id)
        ##rename L1 all groups should be now changed
        _update_group(g1.group_id, 'R1', parent_id=g4.group_id)
        Session().commit()
        self.assertEqual(g1.full_path, 'R1_NEW/R1')
        self.assertEqual(g2.full_path, 'R1_NEW/R1/R2')
        self.assertEqual(g3.full_path, 'R1_NEW/R1/R2/R3')
        self.assertEqual(r.repo_name,  'R1_NEW/R1/R2/R3/R3_REPO')

    def test_change_parent_of_top_level_group_in_nested_setup_with_rename(self):
        g1 = fixture.create_group('X1')
        g2 = fixture.create_group('X2', group_parent_id=g1.group_id)
        g3 = fixture.create_group('X3', group_parent_id=g2.group_id)
        g4 = fixture.create_group('X1_NEW')

        r = fixture.create_repo('X1/X2/X3/X3_REPO', repo_group=g3.group_id)

        ##rename L1 all groups should be now changed
        _update_group(g1.group_id, 'X1_PRIM', parent_id=g4.group_id)
        Session().commit()
        self.assertEqual(g1.full_path, 'X1_NEW/X1_PRIM')
        self.assertEqual(g2.full_path, 'X1_NEW/X1_PRIM/X2')
        self.assertEqual(g3.full_path, 'X1_NEW/X1_PRIM/X2/X3')
        self.assertEqual(r.repo_name,  'X1_NEW/X1_PRIM/X2/X3/X3_REPO')
