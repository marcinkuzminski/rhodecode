"""
Helpers for fixture generation
"""
import os
import unittest
from rhodecode.tests import *
from rhodecode.model.db import Repository, User
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel


class Fixture(object):

    def __init__(self):
        pass

    def create_repo(self, name, **kwargs):
        form_data = _get_repo_create_params(repo_name=name, **kwargs)
        cur_user = User.get_by_username(TEST_USER_ADMIN_LOGIN)
        RepoModel().create(form_data, cur_user)
        return Repository.get_by_repo_name(name)

    def create_fork(self, repo_to_fork, fork_name, **kwargs):
        repo_to_fork = Repository.get_by_repo_name(repo_to_fork)
        vcs_type = repo_to_fork.repo_type

        form_data = dict(
            repo_name=fork_name,
            repo_name_full=fork_name,
            repo_group=None,
            repo_type=vcs_type,
            description='',
            private=False,
            copy_permissions=False,
            landing_rev='tip',
            update_after_clone=False,
            fork_parent_id=repo_to_fork,
        )
        cur_user = kwargs.get('cur_user', TEST_USER_ADMIN_LOGIN)
        RepoModel().create_fork(form_data, cur_user=cur_user)

        Session().commit()
        return Repository.get_by_repo_name(fork_name)
