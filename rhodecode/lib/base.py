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
from rhodecode.model.scm import ScmModel
from rhodecode import BACKENDS

class BaseController(WSGIController):

    def __before__(self):
        c.rhodecode_version = __version__
        c.rhodecode_name = config.get('rhodecode_title')
        c.ga_code = config.get('rhodecode_ga_code')
        c.repo_name = get_repo_slug(request)
        c.backends = BACKENDS.keys()
        self.cut_off_limit = int(config.get('cut_off_limit'))

        self.sa = meta.Session()
        scm_model = ScmModel(self.sa)
        c.cached_repo_list = scm_model.get_repos()
        #c.unread_journal = scm_model.get_unread_journal()

        if c.repo_name:
            cached_repo = scm_model.get(c.repo_name)
            if cached_repo:
                c.repository_tags = cached_repo.tags
                c.repository_branches = cached_repo.branches
                c.repository_followers = scm_model.get_followers(cached_repo.dbrepo.repo_id)
                c.repository_forks = scm_model.get_forks(cached_repo.dbrepo.repo_id)
            else:
                c.repository_tags = {}
                c.repository_branches = {}
                c.repository_followers = 0
                c.repository_forks = 0


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
