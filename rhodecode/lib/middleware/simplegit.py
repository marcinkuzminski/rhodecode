# -*- coding: utf-8 -*-
"""
    rhodecode.lib.middleware.simplegit
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    SimpleGit middleware for handling git protocol request (push/clone etc.)
    It's implemented with basic auth function    
    
    :created_on: Apr 28, 2010
    :author: marcink
    :copyright: (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
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

import os
import logging
import traceback

from dulwich import server as dulserver

class SimpleGitUploadPackHandler(dulserver.UploadPackHandler):

    def handle(self):
        write = lambda x: self.proto.write_sideband(1, x)

        graph_walker = dulserver.ProtocolGraphWalker(self, self.repo.object_store,
            self.repo.get_peeled)
        objects_iter = self.repo.fetch_objects(
          graph_walker.determine_wants, graph_walker, self.progress,
          get_tagged=self.get_tagged)

        # Do they want any objects?
        if len(objects_iter) == 0:
            return

        self.progress("counting objects: %d, done.\n" % len(objects_iter))
        dulserver.write_pack_data(dulserver.ProtocolFile(None, write), objects_iter,
                        len(objects_iter))
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

from paste.auth.basic import AuthBasicAuthenticator
from paste.httpheaders import REMOTE_USER, AUTH_TYPE

from rhodecode.lib.auth import authfunc, HasPermissionAnyMiddleware
from rhodecode.lib.utils import invalidate_cache, check_repo_fast
from rhodecode.model.user import UserModel

from webob.exc import HTTPNotFound, HTTPForbidden, HTTPInternalServerError

log = logging.getLogger(__name__)

def is_git(environ):
    """Returns True if request's target is git server. ``HTTP_USER_AGENT`` would
    then have git client version given.
    
    :param environ:
    """
    http_user_agent = environ.get('HTTP_USER_AGENT')
    if http_user_agent and http_user_agent.startswith('git'):
        return True
    return False

class SimpleGit(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        #authenticate this git request using 
        self.authenticate = AuthBasicAuthenticator('', authfunc)
        self.ipaddr = '0.0.0.0'
        self.repository = None
        self.username = None
        self.action = None

    def __call__(self, environ, start_response):
        if not is_git(environ):
            return self.application(environ, start_response)

        proxy_key = 'HTTP_X_REAL_IP'
        def_key = 'REMOTE_ADDR'
        self.ipaddr = environ.get(proxy_key, environ.get(def_key, '0.0.0.0'))
        # skip passing error to error controller
        environ['pylons.status_code_redirect'] = True
        #===================================================================
        # AUTHENTICATE THIS GIT REQUEST
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

        #=======================================================================
        # GET REPOSITORY
        #=======================================================================
        try:
            repo_name = '/'.join(environ['PATH_INFO'].split('/')[1:])
            if repo_name.endswith('/'):
                repo_name = repo_name.rstrip('/')
            self.repository = repo_name
        except:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)

        #===================================================================
        # CHECK PERMISSIONS FOR THIS REQUEST
        #===================================================================
        self.action = self.__get_action(environ)
        if self.action:
            username = self.__get_environ_user(environ)
            try:
                user = self.__get_user(username)
                self.username = user.username
            except:
                log.error(traceback.format_exc())
                return HTTPInternalServerError()(environ, start_response)

            #check permissions for this repository
            if self.action == 'push':
                if not HasPermissionAnyMiddleware('repository.write',
                                                  'repository.admin')\
                                                    (user, repo_name):
                    return HTTPForbidden()(environ, start_response)

            else:
                #any other action need at least read permission
                if not HasPermissionAnyMiddleware('repository.read',
                                                  'repository.write',
                                                  'repository.admin')\
                                                    (user, repo_name):
                    return HTTPForbidden()(environ, start_response)

        self.extras = {'ip':self.ipaddr,
                       'username':self.username,
                       'action':self.action,
                       'repository':self.repository}

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
        except:
            log.error(traceback.format_exc())
            return HTTPInternalServerError()(environ, start_response)

        #invalidate cache on push
        if self.action == 'push':
            self.__invalidate_cache(self.repo_name)
            messages = []
            messages.append('thank you for using rhodecode')
            return app(environ, start_response)
        else:
            return app(environ, start_response)


    def __make_app(self):
        backend = dulserver.DictBackend({'/' + self.repo_name: Repo(self.repo_path)})
        gitserve = HTTPGitApplication(backend)

        return gitserve

    def __get_environ_user(self, environ):
        return environ.get('REMOTE_USER')

    def __get_user(self, username):
        return UserModel().get_by_username(username, cache=True)

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

            return mapping.get(service_cmd, service_cmd if service_cmd else 'other')
        else:
            return 'other'

    def __invalidate_cache(self, repo_name):
        """we know that some change was made to repositories and we should
        invalidate the cache to see the changes right away but only for
        push requests"""
        invalidate_cache('get_repo_cached_%s' % repo_name)
