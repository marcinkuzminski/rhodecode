"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons import config, tmpl_context as c, request, session
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from rhodecode import __version__
from rhodecode.lib import auth
from rhodecode.lib.utils import get_repo_slug
from rhodecode.model import meta
from rhodecode.model.hg import _get_repos_cached, \
    _get_repos_switcher_cached
from vcs import BACKENDS
class BaseController(WSGIController):

    def __before__(self):
        c.rhodecode_version = __version__
        c.rhodecode_name = config['rhodecode_title']
        c.repo_name = get_repo_slug(request)
        c.cached_repo_list = _get_repos_cached()
        c.repo_switcher_list = _get_repos_switcher_cached(c.cached_repo_list)
        c.backends = BACKENDS.keys()
        if c.repo_name:
            cached_repo = c.cached_repo_list.get(c.repo_name)

            if cached_repo:
                c.repository_tags = cached_repo.tags
                c.repository_branches = cached_repo.branches
            else:
                c.repository_tags = {}
                c.repository_branches = {}

        self.sa = meta.Session()

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            #putting this here makes sure that we update permissions every time
            self.rhodecode_user = c.rhodecode_user = auth.get_user(session)
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()
