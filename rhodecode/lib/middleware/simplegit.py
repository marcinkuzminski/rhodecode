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
import logging
import traceback

from dulwich import server as dulserver


class SimpleGitUploadPackHandler(dulserver.UploadPackHandler):

    def handle(self):
        write = lambda x: self.proto.write_sideband(1, x)

        graph_walker = dulserver.ProtocolGraphWalker(self,
                                                     self.repo.object_store,
                                                     self.repo.get_peeled)
        objects_iter = self.repo.fetch_objects(
          graph_walker.determine_wants, graph_walker, self.progress,
          get_tagged=self.get_tagged)

        # Do they want any objects?
        if objects_iter is None or len(objects_iter) == 0:
            return

        self.progress("counting objects: %d, done.\n" % len(objects_iter))
        dulserver.write_pack_objects(dulserver.ProtocolFile(None, write),
                                  objects_iter, len(objects_iter))
        messages = []
        messages.append('thank you for using rhodecode')

        for msg in messages:
            self.progress(msg + "\n")
        # we are done
        self.proto.write("0000")

dulserver.DEFAULT_HANDLERS = {
  'git-upload-pack': SimpleGitUploadPackHandler,
  'git-receive-pack': dulserver.ReceivePackHandler,
}

from dulwich.repo import Repo
from dulwich.web import HTTPGitApplication

from paste.httpheaders import REMOTE_USER, AUTH_TYPE

from rhodecode.lib import safe_str
from rhodecode.lib.base import BaseVCSController
from rhodecode.lib.auth import get_container_username
from rhodecode.lib.utils import is_valid_repo
from rhodecode.model.db import User

from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError

log = logging.getLogger(__name__)


def is_git(environ):
    """Returns True if request's target is git server.
    ``HTTP_USER_AGENT`` would then have git client version given.

    :param environ:
    """
    http_user_agent = environ.get('HTTP_USER_AGENT')
    if http_user_agent and http_user_agent.startswith('git'):
        return True
    return False


class SimpleGit(BaseVCSController):

    def _handle_request(self, environ, start_response):
        if not is_git(environ):
            return self.application(environ, start_response)

        proxy_key = 'HTTP_X_REAL_IP'
        def_key = 'REMOTE_ADDR'
        ipaddr = environ.get(proxy_key, environ.get(def_key, '0.0.0.0'))
        username = None
        # skip passing error to error controller
        environ['pylons.status_code_redirect'] = True

        #======================================================================
        # EXTRACT REPOSITORY NAME FROM ENV
        #======================================================================
        try:
            repo_name = self.__get_repository(environ)
            log.debug('Extracted repo name is %s' % repo_name)
        except:
            return HTTPInternalServerError()(environ, start_response)

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
                                                    repo_name)

            if anonymous_perm is not True or anonymous_user.active is False:
                if anonymous_perm is not True:
                    log.debug('Not enough credentials to access this '
                              'repository as anonymous user')
                if anonymous_user.active is False:
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
                if action in ['pull', 'push']:
                    try:
                        user = self.__get_user(username)
                        if user is None or not user.active:
                            return HTTPForbidden()(environ, start_response)
                        username = user.username
                    except:
                        log.error(traceback.format_exc())
                        return HTTPInternalServerError()(environ,
                                                         start_response)

                    #check permissions for this repository
                    perm = self._check_permission(action, user,
                                                   repo_name)
                    if perm is not True:
                        return HTTPForbidden()(environ, start_response)

        #===================================================================
        # GIT REQUEST HANDLING
        #===================================================================

        repo_path = safe_str(os.path.join(self.basepath, repo_name))
        log.debug('Repository path is %s' % repo_path)

        # quick check if that dir exists...
        if is_valid_repo(repo_name, self.basepath) is False:
            return HTTPNotFound()(environ, start_response)

        try:
            #invalidate cache on push
            if action == 'push':
                self._invalidate_cache(repo_name)
            log.info('%s action on GIT repo "%s"' % (action, repo_name))
            app = self.__make_app(repo_name, repo_path)
            return app(environ, start_response)
        except Exception:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)

    def __make_app(self, repo_name, repo_path):
        """
        Make an wsgi application using dulserver

        :param repo_name: name of the repository
        :param repo_path: full path to the repository
        """

        _d = {'/' + repo_name: Repo(repo_path)}
        backend = dulserver.DictBackend(_d)
        gitserve = HTTPGitApplication(backend)

        return gitserve

    def __get_repository(self, environ):
        """
        Get's repository name out of PATH_INFO header

        :param environ: environ where PATH_INFO is stored
        """
        try:
            environ['PATH_INFO'] = self._get_by_id(environ['PATH_INFO'])
            repo_name = '/'.join(environ['PATH_INFO'].split('/')[1:])
            if repo_name.endswith('/'):
                repo_name = repo_name.rstrip('/')
        except:
            log.error(traceback.format_exc())
            raise
        repo_name = repo_name.split('/')[0]
        return repo_name

    def __get_user(self, username):
        return User.get_by_username(username)

    def __get_action(self, environ):
        """Maps git request commands into a pull or push command.

        :param environ:
        """
        service = environ['QUERY_STRING'].split('=')
        if len(service) > 1:
            service_cmd = service[1]
            mapping = {'git-receive-pack': 'push',
                       'git-upload-pack': 'pull',
                       }

            return mapping.get(service_cmd,
                               service_cmd if service_cmd else 'other')
        else:
            return 'other'
