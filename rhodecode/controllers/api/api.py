import traceback
import logging

from rhodecode.controllers.api import JSONRPCController, JSONRPCError
from rhodecode.lib.auth import HasPermissionAllDecorator
from rhodecode.model.scm import ScmModel

from rhodecode.model.db import User, UsersGroup

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

        try:
            ScmModel().pull_changes(repo, self.rhodecode_user.username)
            return 'Pulled from %s' % repo
        except Exception:
            raise JSONRPCError('Unable to pull changes from "%s"' % repo)


    @HasPermissionAllDecorator('hg.admin')
    def create_user(self, apiuser, username, password, active, admin, name, 
                    lastname, email):
        """
        Creates new user
        
        :param apiuser:
        :param username:
        :param password:
        :param active:
        :param admin:
        :param name:
        :param lastname:
        :param email:
        """
        
        form_data = dict(username=username,
                         password=password,
                         active=active,
                         admin=admin,
                         name=name,
                         lastname=lastname,
                         email=email)
        try:
            u = User.create(form_data)
            return {'id':u.user_id,
                    'msg':'created new user %s' % name}
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create user %s' % name)


    @HasPermissionAllDecorator('hg.admin')
    def create_users_group(self, apiuser, name, active):
        """
        Creates an new usergroup
        
        :param name:
        :param active:
        """
        form_data = {'users_group_name':name,
                     'users_group_active':active}
        try:
            ug = UsersGroup.create(form_data)
            return {'id':ug.users_group_id,
                    'msg':'created new users group %s' % name}
        except Exception:
            log.error(traceback.format_exc())
            raise JSONRPCError('failed to create group %s' % name)
        