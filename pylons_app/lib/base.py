"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons import config, tmpl_context as c, request, session
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons_app import __version__
from pylons_app.lib import auth
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model import meta
from pylons_app.model.hg_model import _get_repos_cached, \
    _get_repos_switcher_cached

class BaseController(WSGIController):
    
    def __before__(self):
        c.hg_app_version = __version__
        c.hg_app_name = config['hg_app_title']
        c.repo_name = get_repo_slug(request)
        c.cached_repo_list = _get_repos_cached()
        c.repo_switcher_list = _get_repos_switcher_cached(c.cached_repo_list)
        
        if c.repo_name:
            cached_repo = c.cached_repo_list.get(c.repo_name)
            
            if cached_repo:
                c.repository_tags = cached_repo.tags
                c.repository_branches = cached_repo.branches
            else:
                c.repository_tags = {}
                c.repository_branches = {}
                    
        self.sa = meta.Session
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            #putting this here makes sure that we update permissions every time
            c.hg_app_user = auth.get_user(session)
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()
