# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.api
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    API controller for RhodeCode

    :created_on: Aug 20, 2011
    :author: marcink
    :copyright: (C) 2011-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.

import traceback
import logging

from sqlalchemy.orm.exc import NoResultFound

from rhodecode.controllers.api import JSONRPCController, JSONRPCError
from rhodecode.lib.auth import HasPermissionAllDecorator, \
    HasPermissionAnyDecorator

from rhodecode.model.meta import Session
from rhodecode.model.scm import ScmModel
from rhodecode.model.db import User, UsersGroup, RepoGroup, Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel
from rhodecode.model.repo_permission import RepositoryPermissionModel
from rhodecode.model.users_group import UsersGroupModel
from rhodecode.model.repos_group import ReposGroupModel


log = logging.getLogger(__name__)


class ApiController(JSONRPCController):
    """
    API Controller


    Each method needs to have USER as argument this is then based on given
    API_KEY propagated as instance of user object

    Preferably this should be first argument also


    Each function should also **raise** JSONRPCError for any
    errors that happens

    """

    @HasPermissionAllDecorator('hg.admin')
    def pull(self, apiuser, repo_name):
        """
        Dispatch pull action on given repo


        :param user:
        :param repo_name:
        """

        if Repository.is_valid(repo_name) is False:
            raise JSONRPCError('Unknown repo "%s"' % repo_name)

        try:
            ScmModel().pull_changes(repo_name, self.rhodecode_user.username)
            return 'Pulled from %s' % repo_name
        except Exception:
            raise JSONRPCError('Unable to pull changes from "%s"' % repo_name)

    @HasPermissionAllDecorator('hg.admin')
    def get_user(self, apiuser, username):
        """"
        Get a user by username

        :param apiuser:
        :param username:
        """

        user = User.get_by_username(username)
        if not user:
            return None

        return dict(
            id=user.user_id,
            username=user.username,
            firstname=user.name,
            lastname=user.lastname,
            email=user.email,
            active=user.active,
            admin=user.admin,
            ldap=user.ldap_dn
        )

    @HasPermissionAllDecorator('hg.admin')
    def get_users(self, apiuser):
        """"
        Get all users

        :param apiuser:
        """

        result = []
        for user in User.getAll():
            result.append(
                dict(
                    id=user.user_id,
                    username=user.username,
                    firstname=user.name,
                    lastname=user.lastname,
                    email=user.email,
                    active=user.active,
                    admin=user.admin,
                    ldap=user.ldap_dn
                )
            )
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_user(self, apiuser, username, password, firstname,
                    lastname, email, active=True, admin=False, ldap_dn=None):
        """
        Create new user or updates current one

        :param apiuser:
        :param username:
        :param password:
        :param name:
        :param lastname:
        :param email:
        :param active:
        :param admin:
        :param ldap_dn:
        """

        if User.get_by_username(username):
            raise JSONRPCError("user %s already exist" % username)

        try:
            usr = UserModel().create_or_update(
                username, password, email, firstname,
                lastname, active, admin, ldap_dn
            )
            Session.commit()
            return dict(
                id=usr.user_id,
                msg='created new user %s' % username
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create user %s' % username)

    @HasPermissionAllDecorator('hg.admin')
    def get_users_group(self, apiuser, group_name):
        """"
        Get users group by name

        :param apiuser:
        :param group_name:
        """

        users_group = UsersGroup.get_by_group_name(group_name)
        if not users_group:
            return None

        members = []
        for user in users_group.members:
            user = user.user
            members.append(dict(id=user.user_id,
                            username=user.username,
                            firstname=user.name,
                            lastname=user.lastname,
                            email=user.email,
                            active=user.active,
                            admin=user.admin,
                            ldap=user.ldap_dn))

        return dict(id=users_group.users_group_id,
                    group_name=users_group.users_group_name,
                    active=users_group.users_group_active,
                    members=members)

    @HasPermissionAllDecorator('hg.admin')
    def get_users_groups(self, apiuser):
        """"
        Get all users groups

        :param apiuser:
        """

        result = []
        for users_group in UsersGroup.getAll():
            members = []
            for user in users_group.members:
                user = user.user
                members.append(dict(id=user.user_id,
                                username=user.username,
                                firstname=user.name,
                                lastname=user.lastname,
                                email=user.email,
                                active=user.active,
                                admin=user.admin,
                                ldap=user.ldap_dn))

            result.append(dict(id=users_group.users_group_id,
                                group_name=users_group.users_group_name,
                                active=users_group.users_group_active,
                                members=members))
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_users_group(self, apiuser, group_name, active=True):
        """
        Creates an new usergroup

        :param group_name:
        :param active:
        """

        if self.get_users_group(apiuser, group_name):
            raise JSONRPCError("users group %s already exist" % group_name)

        try:
            ug = UsersGroupModel().create(name=group_name, active=active)
            Session.commit()
            return dict(id=ug.users_group_id,
                        msg='created new users group %s' % group_name)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create group %s' % group_name)

    @HasPermissionAllDecorator('hg.admin')
    def add_user_to_users_group(self, apiuser, group_name, username):
        """"
        Add a user to a group

        :param apiuser:
        :param group_name:
        :param username:
        """

        try:
            users_group = UsersGroup.get_by_group_name(group_name)
            if not users_group:
                raise JSONRPCError('unknown users group %s' % group_name)

            try:
                user = User.get_by_username(username)
            except NoResultFound:
                raise JSONRPCError('unknown user %s' % username)

            ugm = UsersGroupModel().add_user_to_group(users_group, user)
            Session.commit()
            return dict(id=ugm.users_group_member_id,
                        msg='created new users group member')
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create users group member')

    @HasPermissionAnyDecorator('hg.admin')
    def get_repo(self, apiuser, repo_name):
        """"
        Get repository by name

        :param apiuser:
        :param repo_name:
        """

        repo = Repository.get_by_repo_name(repo_name)
        if repo is None:
            raise JSONRPCError('unknown repository %s' % repo)

        members = []
        for user in repo.repo_to_perm:
            perm = user.permission.permission_name
            user = user.user
            members.append(
                dict(
                    type_="user",
                    id=user.user_id,
                    username=user.username,
                    firstname=user.name,
                    lastname=user.lastname,
                    email=user.email,
                    active=user.active,
                    admin=user.admin,
                    ldap=user.ldap_dn,
                    permission=perm
                )
            )
        for users_group in repo.users_group_to_perm:
            perm = users_group.permission.permission_name
            users_group = users_group.users_group
            members.append(
                dict(
                    type_="users_group",
                    id=users_group.users_group_id,
                    name=users_group.users_group_name,
                    active=users_group.users_group_active,
                    permission=perm
                )
            )

        return dict(
            id=repo.repo_id,
            repo_name=repo.repo_name,
            type=repo.repo_type,
            description=repo.description,
            members=members
        )

    @HasPermissionAnyDecorator('hg.admin')
    def get_repos(self, apiuser):
        """"
        Get all repositories

        :param apiuser:
        """

        result = []
        for repository in Repository.getAll():
            result.append(
                dict(
                    id=repository.repo_id,
                    repo_name=repository.repo_name,
                    type=repository.repo_type,
                    description=repository.description
                )
            )
        return result

    @HasPermissionAnyDecorator('hg.admin')
    def get_repo_nodes(self, apiuser, repo_name, revision, root_path,
                       ret_type='all'):
        """
        returns a list of nodes and it's children
        for a given path at given revision. It's possible to specify ret_type
        to show only files or dirs

        :param apiuser:
        :param repo_name: name of repository
        :param revision: revision for which listing should be done
        :param root_path: path from which start displaying
        :param ret_type: return type 'all|files|dirs' nodes
        """
        try:
            _d, _f = ScmModel().get_nodes(repo_name, revision, root_path,
                                          flat=False)
            _map = {
                'all': _d + _f,
                'files': _f,
                'dirs': _d,
            }
            return _map[ret_type]
        except KeyError:
            raise JSONRPCError('ret_type must be one of %s' % _map.keys())
        except Exception, e:
            raise JSONRPCError(e)

    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def create_repo(self, apiuser, repo_name, owner_name, description='',
                    repo_type='hg', private=False):
        """
        Create a repository

        :param apiuser:
        :param repo_name:
        :param description:
        :param type:
        :param private:
        :param owner_name:
        """

        try:
            try:
                owner = User.get_by_username(owner_name)
            except NoResultFound:
                raise JSONRPCError('unknown user %s' % owner)

            if Repository.get_by_repo_name(repo_name):
                raise JSONRPCError("repo %s already exist" % repo_name)

            groups = repo_name.split('/')
            real_name = groups[-1]
            groups = groups[:-1]
            parent_id = None
            for g in groups:
                group = RepoGroup.get_by_group_name(g)
                if not group:
                    group = ReposGroupModel().create(
                        dict(
                            group_name=g,
                            group_description='',
                            group_parent_id=parent_id
                        )
                    )
                parent_id = group.group_id

            repo = RepoModel().create(
                dict(
                    repo_name=real_name,
                    repo_name_full=repo_name,
                    description=description,
                    private=private,
                    repo_type=repo_type,
                    repo_group=parent_id,
                    clone_uri=None
                ),
                owner
            )
            Session.commit()

            return dict(
                id=repo.repo_id,
                msg="Created new repository %s" % repo.repo_name
            )

        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create repository %s' % repo_name)

    @HasPermissionAnyDecorator('hg.admin')
    def add_user_to_repo(self, apiuser, repo_name, username, perm):
        """
        Add permission for a user to a repository

        :param apiuser:
        :param repo_name:
        :param username:
        :param perm:
        """

        try:
            repo = Repository.get_by_repo_name(repo_name)
            if repo is None:
                raise JSONRPCError('unknown repository %s' % repo)

            try:
                user = User.get_by_username(username)
            except NoResultFound:
                raise JSONRPCError('unknown user %s' % user)

            RepositoryPermissionModel()\
                .update_or_delete_user_permission(repo, user, perm)
            Session.commit()

            return dict(
                msg='Added perm: %s for %s in repo: %s' % (
                    perm, username, repo_name
                )
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission %(repo)s for %(user)s' % dict(
                    user=username, repo=repo_name
                )
            )

    @HasPermissionAnyDecorator('hg.admin')
    def add_users_group_to_repo(self, apiuser, repo_name, group_name, perm):
        """
        Add permission for a users group to a repository

        :param apiuser:
        :param repo_name:
        :param group_name:
        :param perm:
        """

        try:
            repo = Repository.get_by_repo_name(repo_name)
            if repo is None:
                raise JSONRPCError('unknown repository %s' % repo)

            try:
                user_group = UsersGroup.get_by_group_name(group_name)
            except NoResultFound:
                raise JSONRPCError('unknown users group %s' % user_group)

            RepositoryPermissionModel()\
                .update_or_delete_users_group_permission(repo, user_group,
                                                         perm)
            Session.commit()
            return dict(
                msg='Added perm: %s for %s in repo: %s' % (
                    perm, group_name, repo_name
                )
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission %(repo)s for %(usergr)s' % dict(
                    usergr=group_name, repo=repo_name
                )
            )
