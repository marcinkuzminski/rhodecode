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
"""
Created on 2010-04-28

@author: marcink
SimpleHG middleware for handling mercurial protocol request (push/clone etc.)
It's implemented with basic auth function
"""
from itertools import chain
from mercurial.error import RepoError
from mercurial.hgweb import hgweb
from mercurial.hgweb.request import wsgiapplication
from paste.auth.basic import AuthBasicAuthenticator
from paste.httpheaders import REMOTE_USER, AUTH_TYPE
from rhodecode.lib.auth import authfunc, HasPermissionAnyMiddleware, \
    get_user_cached
from rhodecode.lib.utils import is_mercurial, make_ui, invalidate_cache, \
    check_repo_fast, ui_sections
from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError
from rhodecode.lib.utils import action_logger
import logging
import os
import traceback

log = logging.getLogger(__name__)

class SimpleHg(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        #authenticate this mercurial request using 
        self.authenticate = AuthBasicAuthenticator('', authfunc)

    def __call__(self, environ, start_response):
        if not is_mercurial(environ):
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
            repo_name = '/'.join(environ['PATH_INFO'].split('/')[1:])
            if repo_name.endswith('/'):
                repo_name = repo_name.rstrip('/')
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
                                                    (user, repo_name):
                    return HTTPForbidden()(environ, start_response)

            else:
                if not HasPermissionAnyMiddleware('repository.read',
                                                  'repository.write',
                                                  'repository.admin')\
                                                    (user, repo_name):
                    return HTTPForbidden()(environ, start_response)

            #log action    
            proxy_key = 'HTTP_X_REAL_IP'
            def_key = 'REMOTE_ADDR'
            ipaddr = environ.get(proxy_key, environ.get(def_key, '0.0.0.0'))
            self.__log_user_action(user, action, repo_name, ipaddr)

        #===================================================================
        # MERCURIAL REQUEST HANDLING
        #===================================================================
        environ['PATH_INFO'] = '/'#since we wrap into hgweb, reset the path
        self.baseui = make_ui('db')
        self.basepath = self.config['base_path']
        self.repo_path = os.path.join(self.basepath, repo_name)

        #quick check if that dir exists...
        if check_repo_fast(repo_name, self.basepath):
            return HTTPNotFound()(environ, start_response)
        try:
            app = wsgiapplication(self.__make_app)
        except RepoError, e:
            if str(e).find('not found') != -1:
                return HTTPNotFound()(environ, start_response)
        except Exception:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)

        #invalidate cache on push
        if action == 'push':
            self.__invalidate_cache(repo_name)
            messages = []
            messages.append('thank you for using rhodecode')

            return self.msg_wrapper(app, environ, start_response, messages)
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
        hgserve = hgweb(str(self.repo_path), baseui=self.baseui)
        return  self.__load_web_settings(hgserve)

    def __get_environ_user(self, environ):
        return environ.get('REMOTE_USER')

    def __get_user(self, username):
        return get_user_cached(username)

    def __get_action(self, environ):
        """
        Maps mercurial request commands into a pull or push command.
        This should return generally always something
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
                if mapping.has_key(cmd):
                    return mapping[cmd]
                else:
                    return cmd

    def __log_user_action(self, user, action, repo, ipaddr):
        action_logger(user, action, repo, ipaddr)

    def __invalidate_cache(self, repo_name):
        """we know that some change was made to repositories and we should
        invalidate the cache to see the changes right away but only for
        push requests"""
        invalidate_cache('cached_repo_list')
        invalidate_cache('full_changelog', repo_name)


    def __load_web_settings(self, hgserve):
        #set the global ui for hgserve instance passed
        hgserve.repo.ui = self.baseui

        hgrc = os.path.join(self.repo_path, '.hg', 'hgrc')
        repoui = make_ui('file', hgrc, False)


        if repoui:
            #overwrite our ui instance with the section from hgrc file
            for section in ui_sections:
                for k, v in repoui.configitems(section):
                    hgserve.repo.ui.setconfig(section, k, v)

        return hgserve














