import logging

from pylons import tmpl_context as c, app_globals as g, session, request, config, url
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
from webhelpers.paginate import Page

log = logging.getLogger(__name__)

class ShortlogController(BaseController):
    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.repo_name = get_repo_slug(request)
        
    def index(self):
        hg_model = HgModel()
        p = int(request.params.get('page', 1))
        repo = hg_model.get_repo(c.repo_name)
        c.repo_changesets = Page(repo, page=p, items_per_page=20)
        c.shortlog_data = render('shortlog/shortlog_data.html')
        if request.params.get('partial'):
            return c.shortlog_data
        r = render('shortlog/shortlog.html')
        return r
