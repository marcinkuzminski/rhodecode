import logging

from pylons import request, response, session, tmpl_context as c, url, config, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
log = logging.getLogger(__name__)

class ChangesetController(BaseController):
    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.repo_name = get_repo_slug(request)
        
    def index(self):
        # Return a rendered template
        #return render('/changeset.mako')
        # or, return a string
        return 'Hello World'
