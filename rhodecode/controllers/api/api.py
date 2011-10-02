import traceback
import logging

from rhodecode.controllers.api import JSONRPCController, JSONRPCError
from rhodecode.lib.auth import HasPermissionAllDecorator, HasPermissionAnyDecorator
from rhodecode.model.scm import ScmModel

from rhodecode.model.db import User, UsersGroup, UsersGroupMember, Group, Repository
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel
from rhodecode.model.users_group import UsersGroupModel
from rhodecode.model.repo_permission import RepositoryPermissionModel

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
    def pull(self, apiuser, repo):
        """
        Dispatch pull action on given repo


        :param user:
        :param repo:
        """

        if Repository.is_valid(repo) is False:
            raise JSONRPCError('Unknown repo "%s"' % repo)
        
        try:
            ScmModel().pull_changes(repo, self.rhodecode_user.username)
            return 'Pulled from %s' % repo
        except Exception:
            raise JSONRPCError('Unable to pull changes from "%s"' % repo)


    @HasPermissionAllDecorator('hg.admin')
    def list_users(self, apiuser):
        """"
        Lists all users

        :param apiuser
        """

        result = []
        for user in User.getAll():
            result.append( dict(id = user.user_id,
                                username = user.username,
                                firstname = user.name,
                                lastname = user.lastname,
                                email = user.email,
                                active = user.active,
                                admin = user.admin) )
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_user(self, apiuser, username, password, firstname,
                    lastname, email, active=True, admin=False, ldap_dn=None):
        """
        Creates new user

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

        try:
            form_data = dict(username=username,
                             password=password,
                             active=active,
                             admin=admin,
                             name=firstname,
                             lastname=lastname,
                             email=email,
                             ldap_dn=ldap_dn)
            UserModel().create_ldap(username, password, ldap_dn, form_data)
            return dict(msg='created new user %s' % username)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create user %s' % username)

    @HasPermissionAllDecorator('hg.admin')
    def list_users_groups(self, apiuser):
        """"
        Lists all users groups

        :param apiuser
        """

        result = []
        for users_group in UsersGroup.getAll():
            result.append( dict(id=users_group.users_group_id,
                                name=users_group.users_group_name,
                                active=users_group.users_group_active) )
        return result

    @HasPermissionAllDecorator('hg.admin')
    def create_users_group(self, apiuser, name, active=True):
        """
        Creates an new usergroup

        :param name:
        :param active:
        """

        try:
            form_data = dict(users_group_name=name,
                             users_group_active=active)
            ug = UsersGroupModel().create(form_data)
            return dict(id=ug.users_group_id,
                        msg='created new users group %s' % name)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create group %s' % name)

    @HasPermissionAllDecorator('hg.admin')
    def add_user_to_users_group(self, apiuser, user_name, group_name):
        """"
        Add a user to a group

        :param apiuser
        :param user_name
        :param group_name
        """

        try:
            users_group = UsersGroup.get_by_group_name(group_name)
            if not users_group:
                raise JSONRPCError('unknown users group %s' % group_name)

            user = User.by_username(user_name)
            if not user:
                raise JSONRPCError('unknown user %s' % user_name)

            ugm = UsersGroupModel().add_user_to_group(users_group, user)
            return dict(id=ugm.users_group_member_id,
                        msg='created new users group member')
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create users group member')

    @HasPermissionAnyDecorator('hg.admin')
    def list_repos(self, apiuser):
        """"
        Lists all repositories

        :param apiuser
        """
        result = []
        for repository in Repository.getAll():
            result.append( dict(id=repository.repo_id,
                                name=repository.repo_name,
                                type=repository.repo_type,
                                description=repository.description) )
        return result

    @HasPermissionAnyDecorator('hg.admin', 'hg.create.repository')
    def create_repo(self, apiuser, name, owner_name, description=None, repo_type='hg', \
                    private=False, group_name=None):
        """
        Create a repository

        :param apiuser
        :param name
        :param description
        :param type
        :param private
        :param owner_name
        :param group_name
        :param clone
        """

        try:
            if group_name:
                group = Group.get_by_group_name(group_name)
                if group is None:
                    raise JSONRPCError('unknown group %s' % group_name)
            else:
                group = None

            owner = User.by_username(owner_name)
            if owner is None:
                raise JSONRPCError('unknown user %s' % owner)

            RepoModel().create({ "repo_name" : name,
                                 "repo_name_full" : name,
                                 "description" : description,
                                 "private" : private,
                                 "repo_type" : repo_type,
                                 "repo_group" : group,
                                 "clone_uri" : None }, owner)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create repository %s' % name)

    @HasPermissionAnyDecorator('hg.admin')
    def add_user_perm_to_repo(self, apiuser, repo_name, user_name, perm):
        """
        Add permission for a user to a repository

        :param apiuser
        :param repo_name
        :param user_name
        :param perm
        """

        try:
            repo = Repository.by_repo_name(repo_name)
            if repo is None:
                raise JSONRPCError('unknown repository %s' % repo)

            user = User.by_username(user_name)
            if user is None:
                raise JSONRPCError('unknown user %s' % user)

            RepositoryPermissionModel() \
                .updateOrDeleteUserPermission(repo, user, perm)
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to edit permission %(repo)s for %(user)s'
                            % dict( user = user_name, repo = repo_name ) )

