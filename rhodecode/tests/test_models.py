import os
import unittest
from rhodecode.tests import *

from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.db import Group
from sqlalchemy.exc import IntegrityError

class TestReposGroups(unittest.TestCase):

    def setUp(self):
        self.g1 = self.__make_group('test1', skip_if_exists=True)
        self.g2 = self.__make_group('test2', skip_if_exists=True)
        self.g3 = self.__make_group('test3', skip_if_exists=True)

    def tearDown(self):
        print 'out'

    def __check_path(self, *path):
        path = [TESTS_TMP_PATH] + list(path)
        path = os.path.join(*path)
        return os.path.isdir(path)

    def _check_folders(self):
        print os.listdir(TESTS_TMP_PATH)

    def __make_group(self, path, desc='desc', parent_id=None,
                     skip_if_exists=False):

        gr = Group.get_by_group_name(path)
        if gr and skip_if_exists:
            return gr

        form_data = dict(group_name=path,
                         group_description=desc,
                         group_parent_id=parent_id)
        gr = ReposGroupModel().create(form_data)
        return gr

    def __delete_group(self, id_):
        ReposGroupModel().delete(id_)


    def __update_group(self, id_, path, desc='desc', parent_id=None):
        form_data = dict(group_name=path,
                         group_description=desc,
                         group_parent_id=parent_id)

        gr = ReposGroupModel().update(id_, form_data)
        return gr

    def test_create_group(self):
        g = self.__make_group('newGroup')
        self.assertEqual(g.full_path, 'newGroup')

        self.assertTrue(self.__check_path('newGroup'))


    def test_create_same_name_group(self):
        self.assertRaises(IntegrityError, lambda:self.__make_group('newGroup'))


    def test_same_subgroup(self):
        sg1 = self.__make_group('sub1', parent_id=self.g1.group_id)
        self.assertEqual(sg1.parent_group, self.g1)
        self.assertEqual(sg1.full_path, 'test1/sub1')
        self.assertTrue(self.__check_path('test1', 'sub1'))

        ssg1 = self.__make_group('subsub1', parent_id=sg1.group_id)
        self.assertEqual(ssg1.parent_group, sg1)
        self.assertEqual(ssg1.full_path, 'test1/sub1/subsub1')
        self.assertTrue(self.__check_path('test1', 'sub1', 'subsub1'))


    def test_remove_group(self):
        sg1 = self.__make_group('deleteme')
        self.__delete_group(sg1.group_id)

        self.assertEqual(Group.get(sg1.group_id), None)
        self.assertFalse(self.__check_path('deteteme'))

        sg1 = self.__make_group('deleteme', parent_id=self.g1.group_id)
        self.__delete_group(sg1.group_id)

        self.assertEqual(Group.get(sg1.group_id), None)
        self.assertFalse(self.__check_path('test1', 'deteteme'))


    def test_rename_single_group(self):
        sg1 = self.__make_group('initial')

        new_sg1 = self.__update_group(sg1.group_id, 'after')
        self.assertTrue(self.__check_path('after'))
        self.assertEqual(Group.get_by_group_name('initial'), None)


    def test_update_group_parent(self):

        sg1 = self.__make_group('initial', parent_id=self.g1.group_id)

        new_sg1 = self.__update_group(sg1.group_id, 'after', parent_id=self.g1.group_id)
        self.assertTrue(self.__check_path('test1', 'after'))
        self.assertEqual(Group.get_by_group_name('test1/initial'), None)


        new_sg1 = self.__update_group(sg1.group_id, 'after', parent_id=self.g3.group_id)
        self.assertTrue(self.__check_path('test3', 'after'))
        self.assertEqual(Group.get_by_group_name('test3/initial'), None)


        new_sg1 = self.__update_group(sg1.group_id, 'hello')
        self.assertTrue(self.__check_path('hello'))

        self.assertEqual(Group.get_by_group_name('hello'), new_sg1)

