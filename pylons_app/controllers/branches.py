from pylons import tmpl_context as c, app_globals as g
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel
import logging

log = logging.getLogger(__name__)

class BranchesController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(BranchesController, self).__before__()
    
    def index(self):
        hg_model = HgModel()
        c.repo_info = hg_model.get_repo(c.repo_name)
        c.repo_branches = c.repo_info.branches
                
        return render('branches/branches.html')
