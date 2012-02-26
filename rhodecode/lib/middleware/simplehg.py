# -*- coding: utf-8 -*-
"""
    rhodecode.lib.middleware.simplehg
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SimpleHG middleware for handling mercurial protocol request
    (push/clone etc.). It's implemented with basic auth function

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

from mercurial.error import RepoError
from mercurial.hgweb import hgweb_mod

from paste.httpheaders import REMOTE_USER, AUTH_TYPE

from rhodecode.lib import safe_str
from rhodecode.lib.base import BaseVCSController
from rhodecode.lib.auth import get_container_username
from rhodecode.lib.utils import make_ui, is_valid_repo, ui_sections
from rhodecode.model.db import User

from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError

log = logging.getLogger(__name__)


def is_mercurial(environ):
    """Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    http_accept = environ.get('HTTP_ACCEPT')
    if http_accept and http_accept.startswith('application/mercurial'):
        return True
    return False


class SimpleHg(BaseVCSController):

    def _handle_request(self, environ, start_response):
        if not is_mercurial(environ):
            return self.application(environ, start_response)

        proxy_key = 'HTTP_X_REAL_IP'
        def_key = 'REMOTE_ADDR'
        ipaddr = environ.get(proxy_key, environ.get(def_key, '0.0.0.0'))

        # skip passing error to error controller
        environ['pylons.status_code_redirect'] = True

        #======================================================================
        # EXTRACT REPOSITORY NAME FROM ENV
        #======================================================================
        try:
            repo_name = environ['REPO_NAME'] = self.__get_repository(environ)
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

        extras = {'ip': ipaddr,
                  'username': username,
                  'action': action,
                  'repository': repo_name}

        #======================================================================
        # MERCURIAL REQUEST HANDLING
        #======================================================================

        repo_path = safe_str(os.path.join(self.basepath, repo_name))
        log.debug('Repository path is %s' % repo_path)

        baseui = make_ui('db')
        self.__inject_extras(repo_path, baseui, extras)

        # quick check if that dir exists...
        if is_valid_repo(repo_name, self.basepath) is False:
            return HTTPNotFound()(environ, start_response)

        try:
            # invalidate cache on push
            if action == 'push':
                self._invalidate_cache(repo_name)
            log.info('%s action on HG repo "%s"' % (action, repo_name))
            app = self.__make_app(repo_path, baseui, extras)
            return app(environ, start_response)
        except RepoError, e:
            if str(e).find('not found') != -1:
                return HTTPNotFound()(environ, start_response)
        except Exception:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)

    def __make_app(self, repo_name, baseui, extras):
        """
        Make an wsgi application using hgweb, and inject generated baseui
        instance, additionally inject some extras into ui object
        """
        return hgweb_mod.hgweb(repo_name, name=repo_name, baseui=baseui)

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

        return repo_name

    def __get_user(self, username):
        return User.get_by_username(username)

    def __get_action(self, environ):
        """
        Maps mercurial request commands into a clone,pull or push command.
        This should always return a valid command string

        :param environ:
        """
        mapping = {'changegroup': 'pull',
                   'changegroupsubset': 'pull',
                   'stream_out': 'pull',
                   'listkeys': 'pull',
                   'unbundle': 'push',
                   'pushkey': 'push', }
        for qry in environ['QUERY_STRING'].split('&'):
            if qry.startswith('cmd'):
                cmd = qry.split('=')[-1]
                if cmd in mapping:
                    return mapping[cmd]
                else:
                    return 'pull'

    def __inject_extras(self, repo_path, baseui, extras={}):
        """
        Injects some extra params into baseui instance

        also overwrites global settings with those takes from local hgrc file

        :param baseui: baseui instance
        :param extras: dict with extra params to put into baseui
        """

        hgrc = os.path.join(repo_path, '.hg', 'hgrc')

        # make our hgweb quiet so it doesn't print output
        baseui.setconfig('ui', 'quiet', 'true')

        #inject some additional parameters that will be available in ui
        #for hooks
        for k, v in extras.items():
            baseui.setconfig('rhodecode_extras', k, v)

        repoui = make_ui('file', hgrc, False)

        if repoui:
            #overwrite our ui instance with the section from hgrc file
            for section in ui_sections:
                for k, v in repoui.configitems(section):
                    baseui.setconfig(section, k, v)
