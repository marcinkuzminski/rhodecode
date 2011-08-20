from rhodecode.controllers.api import JSONRPCController, JSONRPCError
from rhodecode.lib.auth import HasPermissionAllDecorator
from rhodecode.model.scm import ScmModel


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
    def pull(self, user, repo):
        """
        Dispatch pull action on given repo
        
        
        param user:
        param repo:
        """

        try:
            ScmModel().pull_changes(repo, self.rhodecode_user.username)
            return 'Pulled from %s' % repo
        except Exception:
            raise JSONRPCError('Unable to pull changes from "%s"' % repo)




