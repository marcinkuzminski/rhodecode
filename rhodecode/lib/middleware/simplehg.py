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
from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError, \
    HTTPBadRequest, HTTPNotAcceptable

from rhodecode.lib.utils2 import safe_str, fix_PATH, get_server_url,\
    _set_extras
from rhodecode.lib.base import BaseVCSController
from rhodecode.lib.auth import get_container_username
from rhodecode.lib.utils import make_ui, is_valid_repo, ui_sections
from rhodecode.lib.compat import json
from rhodecode.model.db import User
from rhodecode.lib.exceptions import HTTPLockedRC


log = logging.getLogger(__name__)


def is_mercurial(environ):
    """
    Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    http_accept = environ.get('HTTP_ACCEPT')
    path_info = environ['PATH_INFO']
    if http_accept and http_accept.startswith('application/mercurial'):
        ishg_path = True
    else:
        ishg_path = False

    log.debug('pathinfo: %s detected as HG %s' % (
        path_info, ishg_path)
    )
    return ishg_path


class SimpleHg(BaseVCSController):

    def _handle_request(self, environ, start_response):
        if not is_mercurial(environ):
            return self.application(environ, start_response)
        if not self._check_ssl(environ, start_response):
            return HTTPNotAcceptable('SSL REQUIRED !')(environ, start_response)

        ip_addr = self._get_ip_addr(environ)
        username = None
        # skip passing error to error controller
        environ['pylons.status_code_redirect'] = True

        #======================================================================
        # EXTRACT REPOSITORY NAME FROM ENV
        #======================================================================
        try:
            repo_name = environ['REPO_NAME'] = self.__get_repository(environ)
            log.debug('Extracted repo name is %s' % repo_name)
        except Exception:
            return HTTPInternalServerError()(environ, start_response)

        # quick check if that dir exists...
        if not is_valid_repo(repo_name, self.basepath, 'hg'):
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

        # extras are injected into mercurial UI object and later available
        # in hg hooks executed by rhodecode
        from rhodecode import CONFIG
        server_url = get_server_url(environ)
        extras = {
            'ip': ip_addr,
            'username': username,
            'action': action,
            'repository': repo_name,
            'scm': 'hg',
            'config': CONFIG['__file__'],
            'server_url': server_url,
            'make_lock': None,
            'locked_by': [None, None]
        }
        #======================================================================
        # MERCURIAL REQUEST HANDLING
        #======================================================================
        str_repo_name = safe_str(repo_name)
        repo_path = os.path.join(safe_str(self.basepath), str_repo_name)
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
            log.info('%s action on HG repo "%s" by "%s" from %s' %
                     (action, str_repo_name, safe_str(username), ip_addr))
            app = self.__make_app(repo_path, baseui, extras)
            return app(environ, start_response)
        except RepoError, e:
            if str(e).find('not found') != -1:
                return HTTPNotFound()(environ, start_response)
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
        except Exception:
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

                return 'pull'

        raise Exception('Unable to detect pull/push action !!'
                        'Are you using non standard command or client ?')

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

        repoui = make_ui('file', hgrc, False)

        if repoui:
            #overwrite our ui instance with the section from hgrc file
            for section in ui_sections:
                for k, v in repoui.configitems(section):
                    baseui.setconfig(section, k, v)
        _set_extras(extras)
