#!/usr/bin/env python
# encoding: utf-8
# middleware to handle mercurial api calls
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
from dulwich.repo import Repo
from dulwich.server import DictBackend
from dulwich.web import HTTPGitApplication
from itertools import chain
from paste.auth.basic import AuthBasicAuthenticator
from paste.httpheaders import REMOTE_USER, AUTH_TYPE
from rhodecode.lib.auth import authfunc, HasPermissionAnyMiddleware, \
    get_user_cached
from rhodecode.lib.utils import action_logger, is_git, invalidate_cache, \
    check_repo_fast
from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError
import logging
import os
import traceback
"""
Created on 2010-04-28

@author: marcink
SimpleHG middleware for handling mercurial protocol request (push/clone etc.)
It's implemented with basic auth function
"""




log = logging.getLogger(__name__)

class SimpleGit(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        #authenticate this mercurial request using 
        self.authenticate = AuthBasicAuthenticator('', authfunc)

    def __call__(self, environ, start_response):
        if not is_git(environ):
            return self.application(environ, start_response)

        #===================================================================
        # AUTHENTICATE THIS MERCURIAL REQUEST
        #===================================================================
        username = REMOTE_USER(environ)
        if not username:
            self.authenticate.realm = self.config['rhodecode_realm']
            result = self.authenticate(environ)
            if isinstance(result, str):
                AUTH_TYPE.update(environ, 'basic')
                REMOTE_USER.update(environ, result)
            else:
                return result.wsgi_application(environ, start_response)

        try:
            self.repo_name = environ['PATH_INFO'].split('/')[1]
            if self.repo_name.endswith('/'):
                self.repo_name = self.repo_name.rstrip('/')
        except:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)

        #===================================================================
        # CHECK PERMISSIONS FOR THIS REQUEST
        #===================================================================
        action = self.__get_action(environ)
        if action:
            username = self.__get_environ_user(environ)
            try:
                user = self.__get_user(username)
            except:
                log.error(traceback.format_exc())
                return HTTPInternalServerError()(environ, start_response)

            #check permissions for this repository
            if action == 'push':
                if not HasPermissionAnyMiddleware('repository.write',
                                                  'repository.admin')\
                                                    (user, self.repo_name):
                    return HTTPForbidden()(environ, start_response)

            else:
                #any other action need at least read permission
                if not HasPermissionAnyMiddleware('repository.read',
                                                  'repository.write',
                                                  'repository.admin')\
                                                    (user, self.repo_name):
                    return HTTPForbidden()(environ, start_response)

            #log action
            if action in ('push', 'pull', 'clone'):
                proxy_key = 'HTTP_X_REAL_IP'
                def_key = 'REMOTE_ADDR'
                ipaddr = environ.get(proxy_key, environ.get(def_key, '0.0.0.0'))
                self.__log_user_action(user, action, self.repo_name, ipaddr)

        #===================================================================
        # GIT REQUEST HANDLING
        #===================================================================
        self.basepath = self.config['base_path']
        self.repo_path = os.path.join(self.basepath, self.repo_name)
        #quick check if that dir exists...
        if check_repo_fast(self.repo_name, self.basepath):
            return HTTPNotFound()(environ, start_response)
        try:
            app = self.__make_app()
        except Exception:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)

        #invalidate cache on push
        if action == 'push':
            self.__invalidate_cache(self.repo_name)
            messages = []
            messages.append('thank you for using rhodecode')
            return app(environ, start_response)
            #TODO: check other alternatives for msg wrapping
            #return self.msg_wrapper(app, environ, start_response, messages)
        else:
            return app(environ, start_response)


    def msg_wrapper(self, app, environ, start_response, messages=[]):
        """
        Wrapper for custom messages that come out of mercurial respond messages
        is a list of messages that the user will see at the end of response 
        from merurial protocol actions that involves remote answers
        :param app:
        :param environ:
        :param start_response:
        """
        def custom_messages(msg_list):
            for msg in msg_list:
                yield msg + '\n'
        org_response = app(environ, start_response)
        return chain(org_response, custom_messages(messages))


    def __make_app(self):
        backend = DictBackend({'/' + self.repo_name: Repo(self.repo_path)})
        gitserve = HTTPGitApplication(backend)

        return gitserve

    def __get_environ_user(self, environ):
        return environ.get('REMOTE_USER')

    def __get_user(self, username):
        return get_user_cached(username)

    def __get_action(self, environ):
        """
        Maps git request commands into a pull or push command.
        :param environ:
        """
        service = environ['QUERY_STRING'].split('=')
        if len(service) > 1:
            service_cmd = service[1]
            mapping = {'git-receive-pack': 'pull',
                       'git-upload-pack': 'push',
                       }

            return mapping.get(service_cmd, service_cmd)

    def __log_user_action(self, user, action, repo, ipaddr):
        action_logger(user, action, repo, ipaddr)

    def __invalidate_cache(self, repo_name):
        """we know that some change was made to repositories and we should
        invalidate the cache to see the changes right away but only for
        push requests"""
        invalidate_cache('cached_repo_list')
        invalidate_cache('full_changelog', repo_name)
