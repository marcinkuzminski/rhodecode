"""The base Controller API

Provides the BaseController class for subclassing.
"""
from beaker.cache import cache_region
from pylons import config, tmpl_context as c, request, session
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons_app.lib.auth import LoginRequired, AuthUser
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model import meta
from pylons_app.model.hg_model import HgModel
from pylons_app import __version__

@cache_region('long_term', 'cached_repo_list')
def _get_repos_cached():
    return [rep for rep in HgModel().get_repos()]

@cache_region('long_term', 'full_changelog')
def _full_changelog_cached(repo_name):
    return list(reversed(list(HgModel().get_repo(repo_name))))  

class BaseController(WSGIController):
    
    def __before__(self):
        c.hg_app_version = __version__
        c.repos_prefix = config['hg_app_name']
        c.repo_name = get_repo_slug(request)
        c.hg_app_user = session.get('hg_app_user', AuthUser())
        c.cached_repo_list = _get_repos_cached()
        self.sa = meta.Session
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()
