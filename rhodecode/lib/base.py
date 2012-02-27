"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging
import time
import traceback

from paste.auth.basic import AuthBasicAuthenticator

from pylons import config, tmpl_context as c, request, session, url
from pylons.controllers import WSGIController
from pylons.controllers.util import redirect
from pylons.templating import render_mako as render

from rhodecode import __version__, BACKENDS

from rhodecode.lib import str2bool, safe_unicode
from rhodecode.lib.auth import AuthUser, get_container_username, authfunc,\
    HasPermissionAnyMiddleware, CookieStoreWrapper
from rhodecode.lib.utils import get_repo_slug, invalidate_cache
from rhodecode.model import meta

from rhodecode.model.db import Repository
from rhodecode.model.notification import NotificationModel
from rhodecode.model.scm import ScmModel

log = logging.getLogger(__name__)


class BaseVCSController(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        # base path of repo locations
        self.basepath = self.config['base_path']
        #authenticate this mercurial request using authfunc
        self.authenticate = AuthBasicAuthenticator('', authfunc)
        self.ipaddr = '0.0.0.0'

    def _handle_request(self, environ, start_response):
        raise NotImplementedError()

    def _get_by_id(self, repo_name):
        """
        Get's a special pattern _<ID> from clone url and tries to replace it
        with a repository_name for support of _<ID> non changable urls

        :param repo_name:
        """
        try:
            data = repo_name.split('/')
            if len(data) >= 2:
                by_id = data[1].split('_')
                if len(by_id) == 2 and by_id[1].isdigit():
                    _repo_name = Repository.get(by_id[1]).repo_name
                    data[1] = _repo_name
        except:
            log.debug('Failed to extract repo_name from id %s' % (
                      traceback.format_exc()
                      )
            )

        return '/'.join(data)

    def _invalidate_cache(self, repo_name):
        """
        Set's cache for this repository for invalidation on next access

        :param repo_name: full repo name, also a cache key
        """
        invalidate_cache('get_repo_cached_%s' % repo_name)

    def _check_permission(self, action, user, repo_name):
        """
        Checks permissions using action (push/pull) user and repository
        name

        :param action: push or pull action
        :param user: user instance
        :param repo_name: repository name
        """
        if action == 'push':
            if not HasPermissionAnyMiddleware('repository.write',
                                              'repository.admin')(user,
                                                                  repo_name):
                return False

        else:
            #any other action need at least read permission
            if not HasPermissionAnyMiddleware('repository.read',
                                              'repository.write',
                                              'repository.admin')(user,
                                                                  repo_name):
                return False

        return True

    def __call__(self, environ, start_response):
        start = time.time()
        try:
            return self._handle_request(environ, start_response)
        finally:
            log = logging.getLogger('rhodecode.' + self.__class__.__name__)
            log.debug('Request time: %.3fs' % (time.time() - start))
            meta.Session.remove()


class BaseController(WSGIController):

    def __before__(self):
        c.rhodecode_version = __version__
        c.rhodecode_instanceid = config.get('instance_id')
        c.rhodecode_name = config.get('rhodecode_title')
        c.use_gravatar = str2bool(config.get('use_gravatar'))
        c.ga_code = config.get('rhodecode_ga_code')
        c.repo_name = get_repo_slug(request)
        c.backends = BACKENDS.keys()
        c.unread_notifications = NotificationModel()\
                        .get_unread_cnt_for_user(c.rhodecode_user.user_id)
        self.cut_off_limit = int(config.get('cut_off_limit'))

        self.sa = meta.Session
        self.scm_model = ScmModel(self.sa)

    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']
        start = time.time()
        try:
            # make sure that we update permissions each time we call controller
            api_key = request.GET.get('api_key')
            cookie_store = CookieStoreWrapper(session.get('rhodecode_user'))
            user_id = cookie_store.get('user_id', None)
            username = get_container_username(environ, config)
            auth_user = AuthUser(user_id, api_key, username)
            request.user = auth_user
            self.rhodecode_user = c.rhodecode_user = auth_user
            if not self.rhodecode_user.is_authenticated and \
                       self.rhodecode_user.user_id is not None:
                self.rhodecode_user.set_authenticated(
                    cookie_store.get('is_authenticated')
                )
            log.info('User: %s accessed %s' % (
                auth_user, safe_unicode(environ.get('PATH_INFO')))
            )
            return WSGIController.__call__(self, environ, start_response)
        finally:
            log.info('Request to %s time: %.3fs' % (
                safe_unicode(environ.get('PATH_INFO')), time.time() - start)
            )
            meta.Session.remove()


class BaseRepoController(BaseController):
    """
    Base class for controllers responsible for loading all needed data for
    repository loaded items are

    c.rhodecode_repo: instance of scm repository
    c.rhodecode_db_repo: instance of db
    c.repository_followers: number of followers
    c.repository_forks: number of forks
    """

    def __before__(self):
        super(BaseRepoController, self).__before__()
        if c.repo_name:

            c.rhodecode_db_repo = Repository.get_by_repo_name(c.repo_name)
            c.rhodecode_repo = c.rhodecode_db_repo.scm_instance

            if c.rhodecode_repo is None:
                log.error('%s this repository is present in database but it '
                          'cannot be created as an scm instance', c.repo_name)

                redirect(url('home'))

            c.repository_followers = self.scm_model.get_followers(c.repo_name)
            c.repository_forks = self.scm_model.get_forks(c.repo_name)
