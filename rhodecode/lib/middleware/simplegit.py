# -*- coding: utf-8 -*-
"""
    rhodecode.lib.middleware.simplegit
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SimpleGit middleware for handling git protocol request (push/clone etc.)
    It's implemented with basic auth function

    :created_on: Apr 28, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import logging
import traceback

from dulwich import server as dulserver
from dulwich.web import LimitedInputFilter, GunzipFilter
from rhodecode.lib.exceptions import HTTPLockedRC
from rhodecode.lib.hooks import pre_pull


class SimpleGitUploadPackHandler(dulserver.UploadPackHandler):

    def handle(self):
        write = lambda x: self.proto.write_sideband(1, x)

        graph_walker = dulserver.ProtocolGraphWalker(self,
                                                     self.repo.object_store,
                                                     self.repo.get_peeled)
        objects_iter = self.repo.fetch_objects(
          graph_walker.determine_wants, graph_walker, self.progress,
          get_tagged=self.get_tagged)

        # Did the process short-circuit (e.g. in a stateless RPC call)? Note
        # that the client still expects a 0-object pack in most cases.
        if objects_iter is None:
            return

        self.progress("counting objects: %d, done.\n" % len(objects_iter))
        dulserver.write_pack_objects(dulserver.ProtocolFile(None, write),
                                     objects_iter)
        messages = []
        messages.append('thank you for using rhodecode')

        for msg in messages:
            self.progress(msg + "\n")
        # we are done
        self.proto.write("0000")


dulserver.DEFAULT_HANDLERS = {
  #git-ls-remote, git-clone, git-fetch and git-pull
  'git-upload-pack': SimpleGitUploadPackHandler,
  #git-push
  'git-receive-pack': dulserver.ReceivePackHandler,
}

# not used for now until dulwich get's fixed
#from dulwich.repo import Repo
#from dulwich.web import make_wsgi_chain

from paste.httpheaders import REMOTE_USER, AUTH_TYPE
from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError, \
    HTTPBadRequest, HTTPNotAcceptable

from rhodecode.lib.utils2 import safe_str, fix_PATH, get_server_url,\
    _set_extras
from rhodecode.lib.base import BaseVCSController
from rhodecode.lib.auth import get_container_username
from rhodecode.lib.utils import is_valid_repo, make_ui
from rhodecode.lib.compat import json
from rhodecode.model.db import User, RhodeCodeUi

log = logging.getLogger(__name__)


GIT_PROTO_PAT = re.compile(r'^/(.+)/(info/refs|git-upload-pack|git-receive-pack)')


def is_git(environ):
    path_info = environ['PATH_INFO']
    isgit_path = GIT_PROTO_PAT.match(path_info)
    log.debug('pathinfo: %s detected as GIT %s' % (
        path_info, isgit_path != None)
    )
    return isgit_path


class SimpleGit(BaseVCSController):

    def _handle_request(self, environ, start_response):
        if not is_git(environ):
            return self.application(environ, start_response)
        if not self._check_ssl(environ, start_response):
            return HTTPNotAcceptable('SSL REQUIRED !')(environ, start_response)

        ip_addr = self._get_ip_addr(environ)
        username = None
        self._git_first_op = False
        # skip passing error to error controller
        environ['pylons.status_code_redirect'] = True

        #======================================================================
        # EXTRACT REPOSITORY NAME FROM ENV
        #======================================================================
        try:
            repo_name = self.__get_repository(environ)
            log.debug('Extracted repo name is %s' % repo_name)
        except Exception:
            return HTTPInternalServerError()(environ, start_response)

        # quick check if that dir exists...
        if not is_valid_repo(repo_name, self.basepath, 'git'):
            return HTTPNotFound()(environ, start_response)

        #======================================================================
        # GET ACTION PULL or PUSH
        #======================================================================
        action = self.__get_action(environ)

        #======================================================================
        # CHECK ANONYMOUS PERMISSION
        #======================================================================
        if action in ['pull', 'push']:
            anonymous_user = self.__get_user('default')
            username = anonymous_user.username
            anonymous_perm = self._check_permission(action, anonymous_user,
                                                    repo_name, ip_addr)

            if not anonymous_perm or not anonymous_user.active:
                if not anonymous_perm:
                    log.debug('Not enough credentials to access this '
                              'repository as anonymous user')
                if not anonymous_user.active:
                    log.debug('Anonymous access is disabled, running '
                              'authentication')
                #==============================================================
                # DEFAULT PERM FAILED OR ANONYMOUS ACCESS IS DISABLED SO WE
                # NEED TO AUTHENTICATE AND ASK FOR AUTH USER PERMISSIONS
                #==============================================================

                # Attempting to retrieve username from the container
                username = get_container_username(environ, self.config)

                # If not authenticated by the container, running basic auth
                if not username:
                    self.authenticate.realm = \
                        safe_str(self.config['rhodecode_realm'])
                    result = self.authenticate(environ)
                    if isinstance(result, str):
                        AUTH_TYPE.update(environ, 'basic')
                        REMOTE_USER.update(environ, result)
                        username = result
                    else:
                        return result.wsgi_application(environ, start_response)

                #==============================================================
                # CHECK PERMISSIONS FOR THIS REQUEST USING GIVEN USERNAME
                #==============================================================
                try:
                    user = self.__get_user(username)
                    if user is None or not user.active:
                        return HTTPForbidden()(environ, start_response)
                    username = user.username
                except Exception:
                    log.error(traceback.format_exc())
                    return HTTPInternalServerError()(environ, start_response)

                #check permissions for this repository
                perm = self._check_permission(action, user, repo_name, ip_addr)
                if not perm:
                    return HTTPForbidden()(environ, start_response)

        # extras are injected into UI object and later available
        # in hooks executed by rhodecode
        from rhodecode import CONFIG
        server_url = get_server_url(environ)
        extras = {
            'ip': ip_addr,
            'username': username,
            'action': action,
            'repository': repo_name,
            'scm': 'git',
            'config': CONFIG['__file__'],
            'server_url': server_url,
            'make_lock': None,
            'locked_by': [None, None]
        }

        #===================================================================
        # GIT REQUEST HANDLING
        #===================================================================
        str_repo_name = safe_str(repo_name)
        repo_path = os.path.join(safe_str(self.basepath),str_repo_name)
        log.debug('Repository path is %s' % repo_path)

        # CHECK LOCKING only if it's not ANONYMOUS USER
        if username != User.DEFAULT_USER:
            log.debug('Checking locking on repository')
            (make_lock,
             locked,
             locked_by) = self._check_locking_state(
                            environ=environ, action=action,
                            repo=repo_name, user_id=user.user_id
                       )
            # store the make_lock for later evaluation in hooks
            extras.update({'make_lock': make_lock,
                           'locked_by': locked_by})

        fix_PATH()
        log.debug('HOOKS extras is %s' % extras)
        baseui = make_ui('db')
        self.__inject_extras(repo_path, baseui, extras)

        try:
            self._handle_githooks(repo_name, action, baseui, environ)
            log.info('%s action on GIT repo "%s" by "%s" from %s' %
                     (action, str_repo_name, safe_str(username), ip_addr))
            app = self.__make_app(repo_name, repo_path, extras)
            return app(environ, start_response)
        except HTTPLockedRC, e:
            _code = CONFIG.get('lock_ret_code')
            log.debug('Repository LOCKED ret code %s!' % (_code))
            return e(environ, start_response)
        except Exception:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)
        finally:
            # invalidate cache on push
            if action == 'push':
                self._invalidate_cache(repo_name)

    def __make_app(self, repo_name, repo_path, extras):
        """
        Make an wsgi application using dulserver

        :param repo_name: name of the repository
        :param repo_path: full path to the repository
        """

        from rhodecode.lib.middleware.pygrack import make_wsgi_app
        app = make_wsgi_app(
            repo_root=safe_str(self.basepath),
            repo_name=repo_name,
            extras=extras,
        )
        app = GunzipFilter(LimitedInputFilter(app))
        return app

    def __get_repository(self, environ):
        """
        Get's repository name out of PATH_INFO header

        :param environ: environ where PATH_INFO is stored
        """
        try:
            environ['PATH_INFO'] = self._get_by_id(environ['PATH_INFO'])
            repo_name = GIT_PROTO_PAT.match(environ['PATH_INFO']).group(1)
        except Exception:
            log.error(traceback.format_exc())
            raise

        return repo_name

    def __get_user(self, username):
        return User.get_by_username(username)

    def __get_action(self, environ):
        """
        Maps git request commands into a pull or push command.

        :param environ:
        """
        service = environ['QUERY_STRING'].split('=')

        if len(service) > 1:
            service_cmd = service[1]
            mapping = {
                'git-receive-pack': 'push',
                'git-upload-pack': 'pull',
            }
            op = mapping[service_cmd]
            self._git_stored_op = op
            return op
        else:
            # try to fallback to stored variable as we don't know if the last
            # operation is pull/push
            op = getattr(self, '_git_stored_op', 'pull')
        return op

    def _handle_githooks(self, repo_name, action, baseui, environ):
        """
        Handles pull action, push is handled by post-receive hook
        """
        from rhodecode.lib.hooks import log_pull_action
        service = environ['QUERY_STRING'].split('=')

        if len(service) < 2:
            return

        from rhodecode.model.db import Repository
        _repo = Repository.get_by_repo_name(repo_name)
        _repo = _repo.scm_instance

        _hooks = dict(baseui.configitems('hooks')) or {}
        if action == 'pull':
            # stupid git, emulate pre-pull hook !
            pre_pull(ui=baseui, repo=_repo._repo)
        if action == 'pull' and _hooks.get(RhodeCodeUi.HOOK_PULL):
            log_pull_action(ui=baseui, repo=_repo._repo)

    def __inject_extras(self, repo_path, baseui, extras={}):
        """
        Injects some extra params into baseui instance

        :param baseui: baseui instance
        :param extras: dict with extra params to put into baseui
        """

        _set_extras(extras)
