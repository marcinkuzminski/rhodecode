import logging

from pylons import tmpl_context as c, app_globals as g, session, request, config, url
from pylons.controllers.util import abort, redirect

from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
log = logging.getLogger(__name__)

class SummaryController(BaseController):
    def __before__(self):
        c.repos_prefix = config['repos_name']
        
        c.repo_name = get_repo_slug(request)
        
    def index(self):
        hg_model = HgModel()
        c.repo_info = hg_model.get_repo(c.repo_name)
        c.repo_changesets = c.repo_info.get_changesets(10)
        
        e = request.environ
        uri = r'%(protocol)s://%(user)s@%(host)s/%(repo_name)s' % {
                                                'protocol': e.get('wsgi.url_scheme'),
                                                'user':e.get('REMOTE_USER'),
                                                'host':e.get('HTTP_HOST'),
                                                'repo_name':c.repo_name,
                                                }
        c.clone_repo_url = url(uri)
        #c.repo_tags = c.repo_info.get_tags(limit=10)
        #c.repo_branches = c.repo_info.get_branches(limit=10)
        return render('/summary.html')
