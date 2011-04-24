"""The base Controller API

Provides the BaseController class for subclassing.
"""
from pylons import config, tmpl_context as c, request, session
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from rhodecode import __version__
from rhodecode.lib.auth import AuthUser
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
        self.scm_model = ScmModel(self.sa)
        c.cached_repo_list = self.scm_model.get_repos()
        #c.unread_journal = scm_model.get_unread_journal()

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        try:
            #putting this here makes sure that we update permissions every time
            api_key = request.GET.get('api_key')
            user_id = getattr(session.get('rhodecode_user'), 'user_id', None)
            self.rhodecode_user = c.rhodecode_user = AuthUser(user_id, api_key)
            self.rhodecode_user.set_authenticated(
                                        getattr(session.get('rhodecode_user'),
                                       'is_authenticated', False))
            session['rhodecode_user'] = self.rhodecode_user
            session.save()
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()


class BaseRepoController(BaseController):
    """
    Base class for controllers responsible for loading all needed data
    for those controllers, loaded items are

    c.rhodecode_repo: instance of scm repository (taken from cache)

    """

    def __before__(self):
        super(BaseRepoController, self).__before__()
        if c.repo_name:

            c.rhodecode_repo, dbrepo = self.scm_model.get(c.repo_name,
                                                          retval='repo')

            if c.rhodecode_repo is not None:
                c.repository_followers = self.scm_model.get_followers(c.repo_name)
                c.repository_forks = self.scm_model.get_forks(c.repo_name)
            else:
                c.repository_followers = 0
                c.repository_forks = 0
