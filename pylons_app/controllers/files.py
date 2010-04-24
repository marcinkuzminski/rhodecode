import logging

from pylons import request, response, session, tmpl_context as c, url, config, app_globals as g
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
log = logging.getLogger(__name__)

class FilesController(BaseController):
    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.staticurl = g.statics
        c.repo_name = get_repo_slug(request)

    def index(self, repo_name, revision, f_path):
        hg_model = HgModel()
        c.repo = repo = hg_model.get_repo(c.repo_name)
        c.cur_rev = revision
        c.f_path = f_path
        c.changeset = repo.get_changeset(repo._get_revision('tip'))
        
        
        c.files_list = c.changeset.get_node(f_path)
        
        return render('/files.html')
