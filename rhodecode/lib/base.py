"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging
import time
import traceback

from paste.auth.basic import AuthBasicAuthenticator
from paste.httpexceptions import HTTPUnauthorized, HTTPForbidden
from paste.httpheaders import WWW_AUTHENTICATE, AUTHORIZATION

from pylons import config, tmpl_context as c, request, session, url
from pylons.controllers import WSGIController
from pylons.controllers.util import redirect
from pylons.templating import render_mako as render

from rhodecode import __version__, BACKENDS

from rhodecode.lib.utils2 import str2bool, safe_unicode, AttributeDict,\
    safe_str, safe_int
from rhodecode.lib.auth import AuthUser, get_container_username, authfunc,\
    HasPermissionAnyMiddleware, CookieStoreWrapper
from rhodecode.lib.utils import get_repo_slug
from rhodecode.model import meta

from rhodecode.model.db import Repository, RhodeCodeUi, User, RhodeCodeSetting
from rhodecode.model.notification import NotificationModel
from rhodecode.model.scm import ScmModel
from rhodecode.model.meta import Session

log = logging.getLogger(__name__)


def _filter_proxy(ip):
    """
    HEADERS can have mutliple ips inside the left-most being the original
    client, and each successive proxy that passed the request adding the IP
    address where it received the request from.

    :param ip:
    """
    if ',' in ip:
        _ips = ip.split(',')
        _first_ip = _ips[0].strip()
        log.debug('Got multiple IPs %s, using %s' % (','.join(_ips), _first_ip))
        return _first_ip
    return ip


def _get_ip_addr(environ):
    proxy_key = 'HTTP_X_REAL_IP'
    proxy_key2 = 'HTTP_X_FORWARDED_FOR'
    def_key = 'REMOTE_ADDR'

    ip = environ.get(proxy_key)
    if ip:
        return _filter_proxy(ip)

    ip = environ.get(proxy_key2)
    if ip:
        return _filter_proxy(ip)

    ip = environ.get(def_key, '0.0.0.0')
    return _filter_proxy(ip)


def _get_access_path(environ):
    path = environ.get('PATH_INFO')
    org_req = environ.get('pylons.original_request')
    if org_req:
        path = org_req.environ.get('PATH_INFO')
    return path


class BasicAuth(AuthBasicAuthenticator):

    def __init__(self, realm, authfunc, auth_http_code=None):
        self.realm = realm
        self.authfunc = authfunc
        self._rc_auth_http_code = auth_http_code

    def build_authentication(self):
        head = WWW_AUTHENTICATE.tuples('Basic realm="%s"' % self.realm)
        if self._rc_auth_http_code and self._rc_auth_http_code == '403':
            # return 403 if alternative http return code is specified in
            # RhodeCode config
            return HTTPForbidden(headers=head)
        return HTTPUnauthorized(headers=head)

    def authenticate(self, environ):
        authorization = AUTHORIZATION(environ)
        if not authorization:
            return self.build_authentication()
        (authmeth, auth) = authorization.split(' ', 1)
        if 'basic' != authmeth.lower():
            return self.build_authentication()
        auth = auth.strip().decode('base64')
        _parts = auth.split(':', 1)
        if len(_parts) == 2:
            username, password = _parts
            if self.authfunc(environ, username, password):
                return username
        return self.build_authentication()

    __call__ = authenticate


class BaseVCSController(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        # base path of repo locations
        self.basepath = self.config['base_path']
        #authenticate this mercurial request using authfunc
        self.authenticate = BasicAuth('', authfunc,
                                      config.get('auth_ret_code'))
        self.ip_addr = '0.0.0.0'

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
        except Exception:
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
        ScmModel().mark_for_invalidation(repo_name)

    def _check_permission(self, action, user, repo_name, ip_addr=None):
        """
        Checks permissions using action (push/pull) user and repository
        name

        :param action: push or pull action
        :param user: user instance
        :param repo_name: repository name
        """
        #check IP
        authuser = AuthUser(user_id=user.user_id, ip_addr=ip_addr)
        if not authuser.ip_allowed:
            return False
        else:
            log.info('Access for IP:%s allowed' % (ip_addr))
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

    def _get_ip_addr(self, environ):
        return _get_ip_addr(environ)

    def _check_ssl(self, environ, start_response):
        """
        Checks the SSL check flag and returns False if SSL is not present
        and required True otherwise
        """
        org_proto = environ['wsgi._org_proto']
        #check if we have SSL required  ! if not it's a bad request !
        require_ssl = str2bool(RhodeCodeUi.get_by_key('push_ssl').ui_value)
        if require_ssl and org_proto == 'http':
            log.debug('proto is %s and SSL is required BAD REQUEST !'
                      % org_proto)
            return False
        return True

    def _check_locking_state(self, environ, action, repo, user_id):
        """
        Checks locking on this repository, if locking is enabled and lock is
        present returns a tuple of make_lock, locked, locked_by.
        make_lock can have 3 states None (do nothing) True, make lock
        False release lock, This value is later propagated to hooks, which
        do the locking. Think about this as signals passed to hooks what to do.

        """
        locked = False  # defines that locked error should be thrown to user
        make_lock = None
        repo = Repository.get_by_repo_name(repo)
        user = User.get(user_id)

        # this is kind of hacky, but due to how mercurial handles client-server
        # server see all operation on changeset; bookmarks, phases and
        # obsolescence marker in different transaction, we don't want to check
        # locking on those
        obsolete_call = environ['QUERY_STRING'] in ['cmd=listkeys',]
        locked_by = repo.locked
        if repo and repo.enable_locking and not obsolete_call:
            if action == 'push':
                #check if it's already locked !, if it is compare users
                user_id, _date = repo.locked
                if user.user_id == user_id:
                    log.debug('Got push from user %s, now unlocking' % (user))
                    # unlock if we have push from user who locked
                    make_lock = False
                else:
                    # we're not the same user who locked, ban with 423 !
                    locked = True
            if action == 'pull':
                if repo.locked[0] and repo.locked[1]:
                    locked = True
                else:
                    log.debug('Setting lock on repo %s by %s' % (repo, user))
                    make_lock = True

        else:
            log.debug('Repository %s do not have locking enabled' % (repo))
        log.debug('FINAL locking values make_lock:%s,locked:%s,locked_by:%s'
                  % (make_lock, locked, locked_by))
        return make_lock, locked, locked_by

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
        """
        __before__ is called before controller methods and after __call__
        """
        c.rhodecode_version = __version__
        c.rhodecode_instanceid = config.get('instance_id')
        c.rhodecode_name = config.get('rhodecode_title')
        c.use_gravatar = str2bool(config.get('use_gravatar'))
        c.ga_code = config.get('rhodecode_ga_code')
        # Visual options
        c.visual = AttributeDict({})
        rc_config = RhodeCodeSetting.get_app_settings()

        c.visual.show_public_icon = str2bool(rc_config.get('rhodecode_show_public_icon'))
        c.visual.show_private_icon = str2bool(rc_config.get('rhodecode_show_private_icon'))
        c.visual.stylify_metatags = str2bool(rc_config.get('rhodecode_stylify_metatags'))
        c.visual.lightweight_dashboard = str2bool(rc_config.get('rhodecode_lightweight_dashboard'))
        c.visual.lightweight_dashboard_items = safe_int(config.get('dashboard_items', 100))
        c.visual.repository_fields = str2bool(rc_config.get('rhodecode_repository_fields'))
        c.repo_name = get_repo_slug(request)  # can be empty
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
        try:
            self.ip_addr = _get_ip_addr(environ)
            # make sure that we update permissions each time we call controller
            api_key = request.GET.get('api_key')
            cookie_store = CookieStoreWrapper(session.get('rhodecode_user'))
            user_id = cookie_store.get('user_id', None)
            username = get_container_username(environ, config)
            auth_user = AuthUser(user_id, api_key, username, self.ip_addr)
            request.user = auth_user
            self.rhodecode_user = c.rhodecode_user = auth_user
            if not self.rhodecode_user.is_authenticated and \
                       self.rhodecode_user.user_id is not None:
                self.rhodecode_user.set_authenticated(
                    cookie_store.get('is_authenticated')
                )
            log.info('IP: %s User: %s accessed %s' % (
               self.ip_addr, auth_user, safe_unicode(_get_access_path(environ)))
            )
            return WSGIController.__call__(self, environ, start_response)
        finally:
            meta.Session.remove()


class BaseRepoController(BaseController):
    """
    Base class for controllers responsible for loading all needed data for
    repository loaded items are

    c.rhodecode_repo: instance of scm repository
    c.rhodecode_db_repo: instance of db
    c.repository_followers: number of followers
    c.repository_forks: number of forks
    c.repository_following: weather the current user is following the current repo
    """

    def __before__(self):
        super(BaseRepoController, self).__before__()
        if c.repo_name:

            dbr = c.rhodecode_db_repo = Repository.get_by_repo_name(c.repo_name)
            c.rhodecode_repo = c.rhodecode_db_repo.scm_instance
            # update last change according to VCS data
            dbr.update_changeset_cache(dbr.get_changeset())
            if c.rhodecode_repo is None:
                log.error('%s this repository is present in database but it '
                          'cannot be created as an scm instance', c.repo_name)

                redirect(url('home'))

            # some globals counter for menu
            c.repository_followers = self.scm_model.get_followers(dbr)
            c.repository_forks = self.scm_model.get_forks(dbr)
            c.repository_pull_requests = self.scm_model.get_pull_requests(dbr)
            c.repository_following = self.scm_model.is_following_repo(c.repo_name,
                                                self.rhodecode_user.user_id)
