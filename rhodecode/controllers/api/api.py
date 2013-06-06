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

import time
import traceback
import logging

from rhodecode.controllers.api import JSONRPCController, JSONRPCError
from rhodecode.lib.auth import PasswordGenerator, AuthUser, \
    HasPermissionAllDecorator, HasPermissionAnyDecorator, \
    HasPermissionAnyApi, HasRepoPermissionAnyApi
from rhodecode.lib.utils import map_groups, repo2db_mapper
from rhodecode.lib.utils2 import str2bool, time_to_datetime, safe_int
from rhodecode.model.meta import Session
from rhodecode.model.scm import ScmModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel
from rhodecode.model.users_group import UserGroupModel
from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.db import Repository, RhodeCodeSetting, UserIpMap,\
    Permission, User, Gist
from rhodecode.lib.compat import json
from rhodecode.lib.exceptions import DefaultUserException
from rhodecode.model.gist import GistModel

log = logging.getLogger(__name__)


def store_update(updates, attr, name):
    """
    Stores param in updates dict if it's not instance of Optional
    allows easy updates of passed in params
    """
    if not isinstance(attr, Optional):
        updates[name] = attr


class OptionalAttr(object):
    """
    Special Optional Option that defines other attribute
    """
    def __init__(self, attr_name):
        self.attr_name = attr_name

    def __repr__(self):
        return '<OptionalAttr:%s>' % self.attr_name

    def __call__(self):
        return self
#alias
OAttr = OptionalAttr


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

    :param repoid:
    """
    repo = RepoModel().get_repo(repoid)
    if repo is None:
        raise JSONRPCError('repository `%s` does not exist' % (repoid))
    return repo


def get_repo_group_or_error(repogroupid):
    """
    Get repo group by id or name or return JsonRPCError if not found

    :param repogroupid:
    """
    repo_group = ReposGroupModel()._get_repo_group(repogroupid)
    if repo_group is None:
        raise JSONRPCError(
            'repository group `%s` does not exist' % (repogroupid,))
    return repo_group


def get_users_group_or_error(usersgroupid):
    """
    Get user group by id or name or return JsonRPCError if not found

    :param userid:
    """
    users_group = UserGroupModel().get_group(usersgroupid)
    if users_group is None:
        raise JSONRPCError('user group `%s` does not exist' % usersgroupid)
    return users_group


def get_perm_or_error(permid):
    """
    Get permission by id or name or return JsonRPCError if not found

    :param userid:
    """
    perm = Permission.get_by_key(permid)
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
    def rescan_repos(self, apiuser, remove_obsolete=Optional(False)):
        """
        Dispatch rescan repositories action. If remove_obsolete is set
        than also delete repos that are in database but not in the filesystem.
        aka "clean zombies"

        :param apiuser:
        :param remove_obsolete:
        """

        try:
            rm_obsolete = Optional.extract(remove_obsolete)
            added, removed = repo2db_mapper(ScmModel().repo_scan(),
                                            remove_obsolete=rm_obsolete)
            return {'added': added, 'removed': removed}
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'Error occurred during rescan repositories action'
            )

    def invalidate_cache(self, apiuser, repoid):
        """
        Dispatch cache invalidation action on given repo

        :param apiuser:
        :param repoid:
        """
        repo = get_repo_or_error(repoid)
        if not HasPermissionAnyApi('hg.admin')(user=apiuser):
            # check if we have admin permission for this repo !
            if HasRepoPermissionAnyApi('repository.admin',
                                       'repository.write')(user=apiuser,
                                            repo_name=repo.repo_name) is False:
                raise JSONRPCError('repository `%s` does not exist' % (repoid))

        try:
            ScmModel().mark_for_invalidation(repo.repo_name)
            return ('Caches of repository `%s` was invalidated' % repoid)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'Error occurred during cache invalidation action'
            )

    # permission check inside
    def lock(self, apiuser, repoid, locked=Optional(None),
             userid=Optional(OAttr('apiuser'))):
        """
        Set locking state on particular repository by given user, if
        this command is runned by non-admin account userid is set to user
        who is calling this method

        :param apiuser:
        :param repoid:
        :param userid:
        :param locked:
        """
        repo = get_repo_or_error(repoid)
        if HasPermissionAnyApi('hg.admin')(user=apiuser):
            pass
        elif HasRepoPermissionAnyApi('repository.admin',
                                     'repository.write')(user=apiuser,
                                                         repo_name=repo.repo_name):
            #make sure normal user does not pass someone else userid,
            #he is not allowed to do that
            if not isinstance(userid, Optional) and userid != apiuser.user_id:
                raise JSONRPCError(
                    'userid is not the same as your user'
                )
        else:
            raise JSONRPCError('repository `%s` does not exist' % (repoid))

        if isinstance(userid, Optional):
            userid = apiuser.user_id

        user = get_user_or_error(userid)

        if isinstance(locked, Optional):
            lockobj = Repository.getlock(repo)

            if lockobj[0] is None:
                _d = {
                    'repo': repo.repo_name,
                    'locked': False,
                    'locked_since': None,
                    'locked_by': None,
                    'msg': 'Repo `%s` not locked.' % repo.repo_name
                }
                return _d
            else:
                userid, time_ = lockobj
                lock_user = get_user_or_error(userid)
                _d = {
                    'repo': repo.repo_name,
                    'locked': True,
                    'locked_since': time_,
                    'locked_by': lock_user.username,
                    'msg': ('Repo `%s` locked by `%s`. '
                            % (repo.repo_name,
                               json.dumps(time_to_datetime(time_))))
                }
                return _d

        # force locked state through a flag
        else:
            locked = str2bool(locked)
            try:
                if locked:
                    lock_time = time.time()
                    Repository.lock(repo, user.user_id, lock_time)
                else:
                    lock_time = None
                    Repository.unlock(repo)
                _d = {
                    'repo': repo.repo_name,
                    'locked': locked,
                    'locked_since': lock_time,
                    'locked_by': user.username,
                    'msg': ('User `%s` set lock state for repo `%s` to `%s`'
                            % (user.username, repo.repo_name, locked))
                }
                return _d
            except Exception:
                log.error(traceback.format_exc())
                raise JSONRPCError(
                    'Error occurred locking repository `%s`' % repo.repo_name
                )

    def get_locks(self, apiuser, userid=Optional(OAttr('apiuser'))):
        """
        Get all locks for given userid, if
        this command is runned by non-admin account userid is set to user
        who is calling this method, thus returning locks for himself

        :param apiuser:
        :param userid:
        """

        if not HasPermissionAnyApi('hg.admin')(user=apiuser):
            #make sure normal user does not pass someone else userid,
            #he is not allowed to do that
            if not isinstance(userid, Optional) and userid != apiuser.user_id:
                raise JSONRPCError(
                    'userid is not the same as your user'
                )
        ret = []
        if isinstance(userid, Optional):
            user = None
        else:
            user = get_user_or_error(userid)

        #show all locks
        for r in Repository.getAll():
            userid, time_ = r.locked
            if time_:
                _api_data = r.get_api_data()
                # if we use userfilter just show the locks for this user
                if user:
                    if safe_int(userid) == user.user_id:
                        ret.append(_api_data)
                else:
                    ret.append(_api_data)

        return ret

    @HasPermissionAllDecorator('hg.admin')
    def show_ip(self, apiuser, userid):
        """
        Shows IP address as seen from RhodeCode server, together with all
        defined IP addresses for given user

        :param apiuser:
        :param userid:
        """
        user = get_user_or_error(userid)
        ips = UserIpMap.query().filter(UserIpMap.user == user).all()
        return dict(
            ip_addr_server=self.ip_addr,
            user_ips=ips
        )

    def get_user(self, apiuser, userid=Optional(OAttr('apiuser'))):
        """"
        Get a user by username, or userid, if userid is given

        :param apiuser:
        :param userid:
        """
        if not HasPermissionAnyApi('hg.admin')(user=apiuser):
            #make sure normal user does not pass someone else userid,
            #he is not allowed to do that
            if not isinstance(userid, Optional) and userid != apiuser.user_id:
                raise JSONRPCError(
                    'userid is not the same as your user'
                )

        if isinstance(userid, Optional):
            userid = apiuser.user_id

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
        users_list = User.query().order_by(User.username)\
                        .filter(User.username != User.DEFAULT_USER)\
                        .all()
        for user in users_list:
            result.append(user.get_api_data())
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_user(self, apiuser, username, email, password=Optional(None),
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

        if Optional.extract(ldap_dn):
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

        # call function and store only updated arguments
        updates = {}

        def store_update(attr, name):
            if not isinstance(attr, Optional):
                updates[name] = attr

        try:

            store_update(username, 'username')
            store_update(password, 'password')
            store_update(email, 'email')
            store_update(firstname, 'name')
            store_update(lastname, 'lastname')
            store_update(active, 'active')
            store_update(admin, 'admin')
            store_update(ldap_dn, 'ldap_dn')

            user = UserModel().update_user(user, **updates)
            Session().commit()
            return dict(
                msg='updated user ID:%s %s' % (user.user_id, user.username),
                user=user.get_api_data()
            )
        except DefaultUserException:
            log.error(traceback.format_exc())
            raise JSONRPCError('editing default user is forbidden')
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
        Get user group by name or id

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
        Get all user groups

        :param apiuser:
        """

        result = []
        for users_group in UserGroupModel().get_all():
            result.append(users_group.get_api_data())
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_users_group(self, apiuser, group_name,
                           owner=Optional(OAttr('apiuser')),
                           active=Optional(True)):
        """
        Creates an new usergroup

        :param apiuser:
        :param group_name:
        :param owner:
        :param active:
        """

        if UserGroupModel().get_by_name(group_name):
            raise JSONRPCError("user group `%s` already exist" % group_name)

        try:
            if isinstance(owner, Optional):
                owner = apiuser.user_id

            owner = get_user_or_error(owner)
            active = Optional.extract(active)
            ug = UserGroupModel().create(name=group_name,
                                         owner=owner,
                                         active=active)
            Session().commit()
            return dict(
                msg='created new user group `%s`' % group_name,
                users_group=ug.get_api_data()
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create group `%s`' % group_name)

    @HasPermissionAllDecorator('hg.admin')
    def add_user_to_users_group(self, apiuser, usersgroupid, userid):
        """"
        Add a user to a user group

        :param apiuser:
        :param usersgroupid:
        :param userid:
        """
        user = get_user_or_error(userid)
        users_group = get_users_group_or_error(usersgroupid)

        try:
            ugm = UserGroupModel().add_user_to_group(users_group, user)
            success = True if ugm != True else False
            msg = 'added member `%s` to user group `%s`' % (
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
                'failed to add member to user group `%s`' % (
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
            success = UserGroupModel().remove_user_from_group(users_group,
                                                               user)
            msg = 'removed member `%s` from user group `%s`' % (
                        user.username, users_group.users_group_name
                    )
            msg = msg if success else "User wasn't in group"
            Session().commit()
            return dict(success=success, msg=msg)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to remove member from user group `%s`' % (
                        users_group.users_group_name
                    )
            )

    def get_repo(self, apiuser, repoid):
        """"
        Get repository by name

        :param apiuser:
        :param repoid:
        """
        repo = get_repo_or_error(repoid)

        if not HasPermissionAnyApi('hg.admin')(user=apiuser):
            # check if we have admin permission for this repo !
            if not HasRepoPermissionAnyApi('repository.admin')(user=apiuser,
                                            repo_name=repo.repo_name):
                raise JSONRPCError('repository `%s` does not exist' % (repoid))

        members = []
        followers = []
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

        for user in repo.followers:
            followers.append(user.user.get_api_data())

        data = repo.get_api_data()
        data['members'] = members
        data['followers'] = followers
        return data

    # permission check inside
    def get_repos(self, apiuser):
        """"
        Get all repositories

        :param apiuser:
        """
        result = []
        if HasPermissionAnyApi('hg.admin')(user=apiuser) is False:
            repos = RepoModel().get_all_user_repos(user=apiuser)
        else:
            repos = RepoModel().get_all()

        for repo in repos:
            result.append(repo.get_api_data())
        return result

    @HasPermissionAllDecorator('hg.admin')
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
    def create_repo(self, apiuser, repo_name, owner=Optional(OAttr('apiuser')),
                    repo_type=Optional('hg'),
                    description=Optional(''), private=Optional(False),
                    clone_uri=Optional(None), landing_rev=Optional('tip'),
                    enable_statistics=Optional(False),
                    enable_locking=Optional(False),
                    enable_downloads=Optional(False)):
        """
        Create repository, if clone_url is given it makes a remote clone
        if repo_name is within a group name the groups will be created
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
        if HasPermissionAnyApi('hg.admin')(user=apiuser) is False:
            if not isinstance(owner, Optional):
                #forbid setting owner for non-admins
                raise JSONRPCError(
                    'Only RhodeCode admin can specify `owner` param'
                )
        if isinstance(owner, Optional):
            owner = apiuser.user_id

        owner = get_user_or_error(owner)

        if RepoModel().get_by_repo_name(repo_name):
            raise JSONRPCError("repo `%s` already exist" % repo_name)

        defs = RhodeCodeSetting.get_default_repo_settings(strip_prefix=True)
        if isinstance(private, Optional):
            private = defs.get('repo_private') or Optional.extract(private)
        if isinstance(repo_type, Optional):
            repo_type = defs.get('repo_type')
        if isinstance(enable_statistics, Optional):
            enable_statistics = defs.get('repo_enable_statistics')
        if isinstance(enable_locking, Optional):
            enable_locking = defs.get('repo_enable_locking')
        if isinstance(enable_downloads, Optional):
            enable_downloads = defs.get('repo_enable_downloads')

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
                enable_statistics=enable_statistics,
                enable_downloads=enable_downloads,
                enable_locking=enable_locking
            )

            Session().commit()
            return dict(
                msg="Created new repository `%s`" % (repo.repo_name),
                repo=repo.get_api_data()
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create repository `%s`' % repo_name)

    # permission check inside
    def update_repo(self, apiuser, repoid, name=Optional(None),
                    owner=Optional(OAttr('apiuser')),
                    group=Optional(None),
                    description=Optional(''), private=Optional(False),
                    clone_uri=Optional(None), landing_rev=Optional('tip'),
                    enable_statistics=Optional(False),
                    enable_locking=Optional(False),
                    enable_downloads=Optional(False)):

        """
        Updates repo

        :param apiuser: filled automatically from apikey
        :type apiuser: AuthUser
        :param repoid: repository name or repository id
        :type repoid: str or int
        :param name:
        :param owner:
        :param group:
        :param description:
        :param private:
        :param clone_uri:
        :param landing_rev:
        :param enable_statistics:
        :param enable_locking:
        :param enable_downloads:
        """
        repo = get_repo_or_error(repoid)
        if not HasPermissionAnyApi('hg.admin')(user=apiuser):
            # check if we have admin permission for this repo !
            if not HasRepoPermissionAnyApi('repository.admin')(user=apiuser,
                                                               repo_name=repo.repo_name):
                raise JSONRPCError('repository `%s` does not exist' % (repoid,))

        updates = {
            # update function requires this.
            'repo_name': repo.repo_name
        }
        repo_group = group
        if not isinstance(repo_group, Optional):
            repo_group = get_repo_group_or_error(repo_group)
            repo_group = repo_group.group_id
        try:
            store_update(updates, name, 'repo_name')
            store_update(updates, repo_group, 'repo_group')
            store_update(updates, owner, 'user')
            store_update(updates, description, 'repo_description')
            store_update(updates, private, 'repo_private')
            store_update(updates, clone_uri, 'clone_uri')
            store_update(updates, landing_rev, 'repo_landing_rev')
            store_update(updates, enable_statistics, 'repo_enable_statistics')
            store_update(updates, enable_locking, 'repo_enable_locking')
            store_update(updates, enable_downloads, 'repo_enable_downloads')

            RepoModel().update(repo, **updates)
            Session().commit()
            return dict(
                msg='updated repo ID:%s %s' % (repo.repo_id, repo.repo_name),
                repository=repo.get_api_data()
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to update repo `%s`' % repoid)

    @HasPermissionAnyDecorator('hg.admin', 'hg.fork.repository')
    def fork_repo(self, apiuser, repoid, fork_name, owner=Optional(OAttr('apiuser')),
                  description=Optional(''), copy_permissions=Optional(False),
                  private=Optional(False), landing_rev=Optional('tip')):
        repo = get_repo_or_error(repoid)
        repo_name = repo.repo_name

        _repo = RepoModel().get_by_repo_name(fork_name)
        if _repo:
            type_ = 'fork' if _repo.fork else 'repo'
            raise JSONRPCError("%s `%s` already exist" % (type_, fork_name))

        if HasPermissionAnyApi('hg.admin')(user=apiuser):
            pass
        elif HasRepoPermissionAnyApi('repository.admin',
                                     'repository.write',
                                     'repository.read')(user=apiuser,
                                                        repo_name=repo.repo_name):
            if not isinstance(owner, Optional):
                #forbid setting owner for non-admins
                raise JSONRPCError(
                    'Only RhodeCode admin can specify `owner` param'
                )
        else:
            raise JSONRPCError('repository `%s` does not exist' % (repoid))

        if isinstance(owner, Optional):
            owner = apiuser.user_id

        owner = get_user_or_error(owner)

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

    # perms handled inside
    def delete_repo(self, apiuser, repoid, forks=Optional(None)):
        """
        Deletes a given repository

        :param apiuser:
        :param repoid:
        :param forks: detach or delete, what do do with attached forks for repo
        """
        repo = get_repo_or_error(repoid)

        if HasPermissionAnyApi('hg.admin')(user=apiuser) is False:
            # check if we have admin permission for this repo !
            if HasRepoPermissionAnyApi('repository.admin')(user=apiuser,
                                            repo_name=repo.repo_name) is False:
                raise JSONRPCError('repository `%s` does not exist' % (repoid))

        try:
            handle_forks = Optional.extract(forks)
            _forks_msg = ''
            _forks = [f for f in repo.forks]
            if handle_forks == 'detach':
                _forks_msg = ' ' + 'Detached %s forks' % len(_forks)
            elif handle_forks == 'delete':
                _forks_msg = ' ' + 'Deleted %s forks' % len(_forks)
            elif _forks:
                raise JSONRPCError(
                    'Cannot delete `%s` it still contains attached forks'
                    % repo.repo_name
                )

            RepoModel().delete(repo, forks=forks)
            Session().commit()
            return dict(
                msg='Deleted repository `%s`%s' % (repo.repo_name, _forks_msg),
                success=True
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to delete repository `%s`' % repo.repo_name
            )

    @HasPermissionAllDecorator('hg.admin')
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

    @HasPermissionAllDecorator('hg.admin')
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

    @HasPermissionAllDecorator('hg.admin')
    def grant_users_group_permission(self, apiuser, repoid, usersgroupid,
                                     perm):
        """
        Grant permission for user group on given repository, or update
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
                msg='Granted perm: `%s` for user group: `%s` in '
                    'repo: `%s`' % (
                    perm.permission_name, users_group.users_group_name,
                    repo.repo_name
                ),
                success=True
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission for user group: `%s` in '
                'repo: `%s`' % (
                    usersgroupid, repo.repo_name
                )
            )

    @HasPermissionAllDecorator('hg.admin')
    def revoke_users_group_permission(self, apiuser, repoid, usersgroupid):
        """
        Revoke permission for user group on given repository

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
                msg='Revoked perm for user group: `%s` in repo: `%s`' % (
                    users_group.users_group_name, repo.repo_name
                ),
                success=True
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError(
                'failed to edit permission for user group: `%s` in '
                'repo: `%s`' % (
                    users_group.users_group_name, repo.repo_name
                )
            )

    def create_gist(self, apiuser, files, owner=Optional(OAttr('apiuser')),
                    gist_type=Optional(Gist.GIST_PUBLIC), lifetime=Optional(-1),
                    description=Optional('')):

        try:
            if isinstance(owner, Optional):
                owner = apiuser.user_id

            owner = get_user_or_error(owner)
            description = Optional.extract(description)
            gist_type = Optional.extract(gist_type)
            lifetime = Optional.extract(lifetime)

            # files: {
            #    'filename': {'content':'...', 'lexer': null},
            #    'filename2': {'content':'...', 'lexer': null}
            #}
            gist = GistModel().create(description=description,
                                      owner=owner,
                                      gist_mapping=files,
                                      gist_type=gist_type,
                                      lifetime=lifetime)
            Session().commit()
            return dict(
                msg='created new gist',
                gist=gist.get_api_data()
            )
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create gist')
