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

from rhodecode.controllers.api import JSONRPCController, JSONRPCError
from rhodecode.lib.auth import HasPermissionAllDecorator, \
    HasPermissionAnyDecorator, PasswordGenerator, AuthUser
from rhodecode.lib.utils import map_groups
from rhodecode.model.meta import Session
from rhodecode.model.scm import ScmModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel
from rhodecode.model.users_group import UsersGroupModel
from rhodecode.model.permission import PermissionModel

log = logging.getLogger(__name__)


class Optional(object):
    """
    Defines an optional parameter::

        param = param.getval() if isinstance(param, Optional) else param
        param = param() if isinstance(param, Optional) else param

    is equivalent of::

        param = Optional.extract(param)

    """
    def __init__(self, type_):
        self.type_ = type_

    def __repr__(self):
        return '<Optional:%s>' % self.type_.__repr__()

    def __call__(self):
        return self.getval()

    def getval(self):
        """
        returns value from this Optional instance
        """
        return self.type_

    @classmethod
    def extract(cls, val):
        if isinstance(val, cls):
            return val.getval()
        return val


def get_user_or_error(userid):
    """
    Get user by id or name or return JsonRPCError if not found

    :param userid:
    """
    user = UserModel().get_user(userid)
    if user is None:
        raise JSONRPCError("user `%s` does not exist" % userid)
    return user


def get_repo_or_error(repoid):
    """
    Get repo by id or name or return JsonRPCError if not found

    :param userid:
    """
    repo = RepoModel().get_repo(repoid)
    if repo is None:
        raise JSONRPCError('repository `%s` does not exist' % (repoid))
    return repo


def get_users_group_or_error(usersgroupid):
    """
    Get users group by id or name or return JsonRPCError if not found

    :param userid:
    """
    users_group = UsersGroupModel().get_group(usersgroupid)
    if users_group is None:
        raise JSONRPCError('users group `%s` does not exist' % usersgroupid)
    return users_group


def get_perm_or_error(permid):
    """
    Get permission by id or name or return JsonRPCError if not found

    :param userid:
    """
    perm = PermissionModel().get_permission_by_name(permid)
    if perm is None:
        raise JSONRPCError('permission `%s` does not exist' % (permid))
    return perm


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
    def pull(self, apiuser, repoid):
        """
        Dispatch pull action on given repo

        :param apiuser:
        :param repoid:
        """

        repo = get_repo_or_error(repoid)

        try:
            ScmModel().pull_changes(repo.repo_name,
                                    self.rhodecode_user.username)
            return 'Pulled from `%s`' % repo.repo_name
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'Unable to pull changes from `%s`' % repo.repo_name
            )

    @HasPermissionAllDecorator('hg.admin')
    def get_user(self, apiuser, userid):
        """"
        Get a user by username

        :param apiuser:
        :param userid:
        """

        user = get_user_or_error(userid)
        data = user.get_api_data()
        data['permissions'] = AuthUser(user_id=user.user_id).permissions
        return data

    @HasPermissionAllDecorator('hg.admin')
    def get_users(self, apiuser):
        """"
        Get all users

        :param apiuser:
        """

        result = []
        for user in UserModel().get_all():
            result.append(user.get_api_data())
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_user(self, apiuser, username, email, password,
                    firstname=Optional(None), lastname=Optional(None),
                    active=Optional(True), admin=Optional(False),
                    ldap_dn=Optional(None)):
        """
        Create new user

        :param apiuser:
        :param username:
        :param email:
        :param password:
        :param firstname:
        :param lastname:
        :param active:
        :param admin:
        :param ldap_dn:
        """

        if UserModel().get_by_username(username):
            raise JSONRPCError("user `%s` already exist" % username)

        if UserModel().get_by_email(email, case_insensitive=True):
            raise JSONRPCError("email `%s` already exist" % email)

        if ldap_dn:
            # generate temporary password if ldap_dn
            password = PasswordGenerator().gen_password(length=8)

        try:
            user = UserModel().create_or_update(
                username=Optional.extract(username),
                password=Optional.extract(password),
                email=Optional.extract(email),
                firstname=Optional.extract(firstname),
                lastname=Optional.extract(lastname),
                active=Optional.extract(active),
                admin=Optional.extract(admin),
                ldap_dn=Optional.extract(ldap_dn)
            )
            Session().commit()
            return dict(
                msg='created new user `%s`' % username,
                user=user.get_api_data()
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create user `%s`' % username)

    @HasPermissionAllDecorator('hg.admin')
    def update_user(self, apiuser, userid, username=Optional(None),
                    email=Optional(None), firstname=Optional(None),
                    lastname=Optional(None), active=Optional(None),
                    admin=Optional(None), ldap_dn=Optional(None),
                    password=Optional(None)):
        """
        Updates given user

        :param apiuser:
        :param userid:
        :param username:
        :param email:
        :param firstname:
        :param lastname:
        :param active:
        :param admin:
        :param ldap_dn:
        :param password:
        """

        user = get_user_or_error(userid)

        #return old attribute if Optional is passed. We don't change parameter
        # so user doesn't get updated parameters
        get = lambda attr, name: (
                getattr(user, name) if isinstance(attr, Optional) else attr
        )

        try:

            user = UserModel().create_or_update(
                username=get(username, 'username'),
                password=get(password, 'password'),
                email=get(email, 'email'),
                firstname=get(firstname, 'name'),
                lastname=get(lastname, 'lastname'),
                active=get(active, 'active'),
                admin=get(admin, 'admin'),
                ldap_dn=get(ldap_dn, 'ldap_dn')
            )
            Session().commit()
            return dict(
                msg='updated user ID:%s %s' % (user.user_id, user.username),
                user=user.get_api_data()
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to update user `%s`' % userid)

    @HasPermissionAllDecorator('hg.admin')
    def delete_user(self, apiuser, userid):
        """"
        Deletes an user

        :param apiuser:
        :param userid:
        """
        user = get_user_or_error(userid)

        try:
            UserModel().delete(userid)
            Session().commit()
            return dict(
                msg='deleted user ID:%s %s' % (user.user_id, user.username),
                user=None
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to delete ID:%s %s' % (user.user_id,
                                                              user.username))

    @HasPermissionAllDecorator('hg.admin')
    def get_users_group(self, apiuser, usersgroupid):
        """"
        Get users group by name or id

        :param apiuser:
        :param usersgroupid:
        """
        users_group = get_users_group_or_error(usersgroupid)

        data = users_group.get_api_data()

        members = []
        for user in users_group.members:
            user = user.user
            members.append(user.get_api_data())
        data['members'] = members
        return data

    @HasPermissionAllDecorator('hg.admin')
    def get_users_groups(self, apiuser):
        """"
        Get all users groups

        :param apiuser:
        """

        result = []
        for users_group in UsersGroupModel().get_all():
            result.append(users_group.get_api_data())
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_users_group(self, apiuser, group_name, active=Optional(True)):
        """
        Creates an new usergroup

        :param apiuser:
        :param group_name:
        :param active:
        """

        if UsersGroupModel().get_by_name(group_name):
            raise JSONRPCError("users group `%s` already exist" % group_name)

        try:
            active = Optional.extract(active)
            ug = UsersGroupModel().create(name=group_name, active=active)
            Session().commit()
            return dict(
                msg='created new users group `%s`' % group_name,
                users_group=ug.get_api_data()
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create group `%s`' % group_name)

    @HasPermissionAllDecorator('hg.admin')
    def add_user_to_users_group(self, apiuser, usersgroupid, userid):
        """"
        Add a user to a users group

        :param apiuser:
        :param usersgroupid:
        :param userid:
        """
        user = get_user_or_error(userid)
        users_group = get_users_group_or_error(usersgroupid)

        try:
            ugm = UsersGroupModel().add_user_to_group(users_group, user)
            success = True if ugm != True else False
            msg = 'added member `%s` to users group `%s`' % (
                        user.username, users_group.users_group_name
                    )
            msg = msg if success else 'User is already in that group'
            Session().commit()

            return dict(
                success=success,
                msg=msg
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to add member to users group `%s`' % (
                    users_group.users_group_name
                )
            )

    @HasPermissionAllDecorator('hg.admin')
    def remove_user_from_users_group(self, apiuser, usersgroupid, userid):
        """
        Remove user from a group

        :param apiuser:
        :param usersgroupid:
        :param userid:
        """
        user = get_user_or_error(userid)
        users_group = get_users_group_or_error(usersgroupid)

        try:
            success = UsersGroupModel().remove_user_from_group(users_group,
                                                               user)
            msg = 'removed member `%s` from users group `%s`' % (
                        user.username, users_group.users_group_name
                    )
            msg = msg if success else "User wasn't in group"
            Session().commit()
            return dict(success=success, msg=msg)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to remove member from users group `%s`' % (
                        users_group.users_group_name
                    )
            )

    @HasPermissionAnyDecorator('hg.admin')
    def get_repo(self, apiuser, repoid):
        """"
        Get repository by name

        :param apiuser:
        :param repoid:
        """
        repo = get_repo_or_error(repoid)

        members = []
        for user in repo.repo_to_perm:
            perm = user.permission.permission_name
            user = user.user
            user_data = user.get_api_data()
            user_data['type'] = "user"
            user_data['permission'] = perm
            members.append(user_data)

        for users_group in repo.users_group_to_perm:
            perm = users_group.permission.permission_name
            users_group = users_group.users_group
            users_group_data = users_group.get_api_data()
            users_group_data['type'] = "users_group"
            users_group_data['permission'] = perm
            members.append(users_group_data)

        data = repo.get_api_data()
        data['members'] = members
        return data

    @HasPermissionAnyDecorator('hg.admin')
    def get_repos(self, apiuser):
        """"
        Get all repositories

        :param apiuser:
        """

        result = []
        for repo in RepoModel().get_all():
            result.append(repo.get_api_data())
        return result

    @HasPermissionAnyDecorator('hg.admin')
    def get_repo_nodes(self, apiuser, repoid, revision, root_path,
                       ret_type='all'):
        """
        returns a list of nodes and it's children
        for a given path at given revision. It's possible to specify ret_type
        to show only files or dirs

        :param apiuser:
        :param repoid: name or id of repository
        :param revision: revision for which listing should be done
        :param root_path: path from which start displaying
        :param ret_type: return type 'all|files|dirs' nodes
        """
        repo = get_repo_or_error(repoid)
        try:
            _d, _f = ScmModel().get_nodes(repo, revision, root_path,
                                          flat=False)
            _map = {
                'all': _d + _f,
                'files': _f,
                'dirs': _d,
            }
            return _map[ret_type]
        except KeyError:
            raise JSONRPCError('ret_type must be one of %s' % _map.keys())
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to get repo: `%s` nodes' % repo.repo_name
            )

    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def create_repo(self, apiuser, repo_name, owner, repo_type,
                    description=Optional(''), private=Optional(False),
                    clone_uri=Optional(None), landing_rev=Optional('tip')):
        """
        Create repository, if clone_url is given it makes a remote clone
        if repo_name is withina  group name the groups will be created
        automatically if they aren't present

        :param apiuser:
        :param repo_name:
        :param onwer:
        :param repo_type:
        :param description:
        :param private:
        :param clone_uri:
        :param landing_rev:
        """
        owner = get_user_or_error(owner)

        if RepoModel().get_by_repo_name(repo_name):
            raise JSONRPCError("repo `%s` already exist" % repo_name)

        private = Optional.extract(private)
        clone_uri = Optional.extract(clone_uri)
        description = Optional.extract(description)
        landing_rev = Optional.extract(landing_rev)

        try:
            # create structure of groups and return the last group
            group = map_groups(repo_name)

            repo = RepoModel().create_repo(
                repo_name=repo_name,
                repo_type=repo_type,
                description=description,
                owner=owner,
                private=private,
                clone_uri=clone_uri,
                repos_group=group,
                landing_rev=landing_rev,
            )

            Session().commit()

            return dict(
                msg="Created new repository `%s`" % (repo.repo_name),
                repo=repo.get_api_data()
            )

        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create repository `%s`' % repo_name)

    @HasPermissionAnyDecorator('hg.admin')
    def fork_repo(self, apiuser, repoid, fork_name, owner,
                  description=Optional(''), copy_permissions=Optional(False),
                  private=Optional(False), landing_rev=Optional('tip')):
        repo = get_repo_or_error(repoid)
        repo_name = repo.repo_name
        owner = get_user_or_error(owner)

        _repo = RepoModel().get_by_repo_name(fork_name)
        if _repo:
            type_ = 'fork' if _repo.fork else 'repo'
            raise JSONRPCError("%s `%s` already exist" % (type_, fork_name))

        try:
            # create structure of groups and return the last group
            group = map_groups(fork_name)

            form_data = dict(
                repo_name=fork_name,
                repo_name_full=fork_name,
                repo_group=group,
                repo_type=repo.repo_type,
                description=Optional.extract(description),
                private=Optional.extract(private),
                copy_permissions=Optional.extract(copy_permissions),
                landing_rev=Optional.extract(landing_rev),
                update_after_clone=False,
                fork_parent_id=repo.repo_id,
            )
            RepoModel().create_fork(form_data, cur_user=owner)
            return dict(
                msg='Created fork of `%s` as `%s`' % (repo.repo_name,
                                                      fork_name),
                success=True  # cannot return the repo data here since fork
                              # cann be done async
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to fork repository `%s` as `%s`' % (repo_name,
                                                            fork_name)
            )

    @HasPermissionAnyDecorator('hg.admin')
    def delete_repo(self, apiuser, repoid):
        """
        Deletes a given repository

        :param apiuser:
        :param repoid:
        """
        repo = get_repo_or_error(repoid)

        try:
            RepoModel().delete(repo)
            Session().commit()
            return dict(
                msg='Deleted repository `%s`' % repo.repo_name,
                success=True
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to delete repository `%s`' % repo.repo_name
            )

    @HasPermissionAnyDecorator('hg.admin')
    def grant_user_permission(self, apiuser, repoid, userid, perm):
        """
        Grant permission for user on given repository, or update existing one
        if found

        :param repoid:
        :param userid:
        :param perm:
        """
        repo = get_repo_or_error(repoid)
        user = get_user_or_error(userid)
        perm = get_perm_or_error(perm)

        try:

            RepoModel().grant_user_permission(repo=repo, user=user, perm=perm)

            Session().commit()
            return dict(
                msg='Granted perm: `%s` for user: `%s` in repo: `%s`' % (
                    perm.permission_name, user.username, repo.repo_name
                ),
                success=True
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission for user: `%s` in repo: `%s`' % (
                    userid, repoid
                )
            )

    @HasPermissionAnyDecorator('hg.admin')
    def revoke_user_permission(self, apiuser, repoid, userid):
        """
        Revoke permission for user on given repository

        :param apiuser:
        :param repoid:
        :param userid:
        """

        repo = get_repo_or_error(repoid)
        user = get_user_or_error(userid)
        try:

            RepoModel().revoke_user_permission(repo=repo, user=user)

            Session().commit()
            return dict(
                msg='Revoked perm for user: `%s` in repo: `%s`' % (
                    user.username, repo.repo_name
                ),
                success=True
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission for user: `%s` in repo: `%s`' % (
                    userid, repoid
                )
            )

    @HasPermissionAnyDecorator('hg.admin')
    def grant_users_group_permission(self, apiuser, repoid, usersgroupid,
                                     perm):
        """
        Grant permission for users group on given repository, or update
        existing one if found

        :param apiuser:
        :param repoid:
        :param usersgroupid:
        :param perm:
        """
        repo = get_repo_or_error(repoid)
        perm = get_perm_or_error(perm)
        users_group = get_users_group_or_error(usersgroupid)

        try:
            RepoModel().grant_users_group_permission(repo=repo,
                                                     group_name=users_group,
                                                     perm=perm)

            Session().commit()
            return dict(
                msg='Granted perm: `%s` for users group: `%s` in '
                    'repo: `%s`' % (
                    perm.permission_name, users_group.users_group_name,
                    repo.repo_name
                ),
                success=True
            )
        except Exception:
            print traceback.format_exc()
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission for users group: `%s` in '
                'repo: `%s`' % (
                    usersgroupid, repo.repo_name
                )
            )

    @HasPermissionAnyDecorator('hg.admin')
    def revoke_users_group_permission(self, apiuser, repoid, usersgroupid):
        """
        Revoke permission for users group on given repository

        :param apiuser:
        :param repoid:
        :param usersgroupid:
        """
        repo = get_repo_or_error(repoid)
        users_group = get_users_group_or_error(usersgroupid)

        try:
            RepoModel().revoke_users_group_permission(repo=repo,
                                                      group_name=users_group)

            Session().commit()
            return dict(
                msg='Revoked perm for users group: `%s` in repo: `%s`' % (
                    users_group.users_group_name, repo.repo_name
                ),
                success=True
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission for users group: `%s` in '
                'repo: `%s`' % (
                    users_group.users_group_name, repo.repo_name
                )
            )
