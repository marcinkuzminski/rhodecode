"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons import config, tmpl_context as c, request, session
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons_app.lib.auth import LoginRequired, AuthUser
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model import meta
from pylons_app.model.hg_model import _get_repos_cached
from pylons_app import __version__

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
