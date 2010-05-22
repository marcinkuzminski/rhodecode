from pylons import request, response, session, tmpl_context as c, url, config, \
    app_globals as g
from pylons.controllers.util import abort, redirect
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
import logging


log = logging.getLogger(__name__)

class ChangesetController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(ChangesetController, self).__before__()
        
    def index(self, revision):
        hg_model = HgModel()
        c.changeset = hg_model.get_repo(c.repo_name).get_changeset(revision)
                          
        return render('changeset/changeset.html')
