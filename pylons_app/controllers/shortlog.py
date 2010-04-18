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
        c.staticurl = g.statics
        c.repo_name = get_repo_slug(request)
        
        
    def index(self):
        hg_model = HgModel()
        lim = 20
        p = int(request.params.get('page', 1))
        repo = hg_model.get_repo(c.repo_name)
        cnt = repo.revisions[-1]
        gen = repo.get_changesets(None)
        repo_changesets = list(gen)
        repo_changesets2 = list(gen)
        repo_changesets3 = list(gen)
        repo_changesets4 = list(gen)
         
        c.repo_changesets = Page(repo_changesets, page=p, item_count=cnt, items_per_page=lim)
        c.shortlog_data = render('shortlog_data.html')
        if request.params.get('partial'):
            return c.shortlog_data
        return render('/shortlog.html')
