"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons_app.model import meta
from beaker.cache import cache_region
from pylons import tmpl_context as c
from pylons_app.model.hg_model import HgModel

@cache_region('long_term', 'repo_list_2')
def _get_repos():
    return [rep['name'] for rep in HgModel().get_repos()]

class BaseController(WSGIController):
        
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        c.repo_list = _get_repos()
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()
