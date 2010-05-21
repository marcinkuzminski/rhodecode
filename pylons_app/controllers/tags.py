import logging

from pylons import tmpl_context as c, app_globals as g, session, request, config, url
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
from pylons_app.lib.auth import LoginRequired
log = logging.getLogger(__name__)


class TagsController(BaseController):
    
    @LoginRequired()
    def __before__(self):
        super(TagsController, self).__before__()
        
    def index(self):
        hg_model = HgModel()
        c.repo_info = hg_model.get_repo(c.repo_name)
        c.repo_tags = c.repo_info.tags
        
        return render('tags/tags.html')
