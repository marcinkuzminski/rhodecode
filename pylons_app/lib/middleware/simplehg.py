#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 marcink.  All rights reserved.
#
"""
Created on 2010-04-28

@author: marcink
SimpleHG middleware for handling mercurial protocol request (push/clone etc.)
It's implemented with basic auth function
"""
from datetime import datetime
from mercurial.hgweb import hgweb
from mercurial.hgweb.request import wsgiapplication
from paste.auth.basic import AuthBasicAuthenticator
from paste.httpheaders import REMOTE_USER, AUTH_TYPE
from pylons_app.lib.auth import authfunc
from pylons_app.lib.utils import is_mercurial, make_ui, invalidate_cache
from pylons_app.model import meta
from pylons_app.model.db import UserLogs, Users
from webob.exc import HTTPNotFound
import logging
import os
log = logging.getLogger(__name__)

class SimpleHg(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        #authenticate this mercurial request using 
        realm = '%s %s' % (config['hg_app_name'], 'mercurial repository')
        self.authenticate = AuthBasicAuthenticator(realm, authfunc)
        
    def __call__(self, environ, start_response):
        if not is_mercurial(environ):
            return self.application(environ, start_response)
        else:
            #===================================================================
            # AUTHENTICATE THIS MERCURIAL REQUEST
            #===================================================================
            username = REMOTE_USER(environ)
            if not username:
                result = self.authenticate(environ)
                if isinstance(result, str):
                    AUTH_TYPE.update(environ, 'basic')
                    REMOTE_USER.update(environ, result)
                else:
                    return result.wsgi_application(environ, start_response)
            
            try:
                repo_name = environ['PATH_INFO'].split('/')[1]
            except:
                return HTTPNotFound()(environ, start_response)
            
            #since we wrap into hgweb, just reset the path
            environ['PATH_INFO'] = '/'
            self.baseui = make_ui()
            self.basepath = self.baseui.configitems('paths')[0][1]\
                                                            .replace('*', '')
            self.repo_path = os.path.join(self.basepath, repo_name)
            try:
                app = wsgiapplication(self.__make_app)
            except Exception as e:
                return HTTPNotFound()(environ, start_response)
            action = self.__get_action(environ)            
            #invalidate cache on push
            if action == 'push':
                self.__invalidate_cache(repo_name)
            
            if action:
                username = self.__get_environ_user(environ)
                self.__log_user_action(username, action, repo_name)
                         
            return app(environ, start_response)            

    def __make_app(self):
        hgserve = hgweb(self.repo_path)
        return  self.__load_web_settings(hgserve)
    
    def __get_environ_user(self, environ):
        return environ.get('REMOTE_USER')
        
    def __get_action(self, environ):
        """
        Maps mercurial request commands into a pull or push command.
        @param environ:
        """
        mapping = {
            'changegroup': 'pull',
            'changegroupsubset': 'pull',
            'unbundle': 'push',
            'stream_out': 'pull',
        }                    
        for qry in environ['QUERY_STRING'].split('&'):
            if qry.startswith('cmd'):
                cmd = qry.split('=')[-1]
                if mapping.has_key(cmd):
                    return mapping[cmd]
    
    def __log_user_action(self, username, action, repo):
        sa = meta.Session
        try:
            user = sa.query(Users)\
                    .filter(Users.username == username).one()
            user_log = UserLogs()
            user_log.user_id = user.user_id
            user_log.action = action
            user_log.repository = repo.replace('/', '')
            user_log.action_date = datetime.now()
            sa.add(user_log)
            sa.commit()
            log.info('Adding user %s, action %s on %s',
                                            username, action, repo)
        except Exception as e:
            sa.rollback()
            log.error('could not log user action:%s', str(e))
    
    def __invalidate_cache(self, repo_name):
        """we know that some change was made to repositories and we should
        invalidate the cache to see the changes right away but only for
        push requests"""
        invalidate_cache('cached_repo_list')
        invalidate_cache('full_changelog', repo_name)
           
                   
    def __load_web_settings(self, hgserve):
        repoui = make_ui(os.path.join(self.repo_path, '.hg', 'hgrc'), False)
        #set the global ui for hgserve
        hgserve.repo.ui = self.baseui
        
        if repoui:
            #set the repository based config
            hgserve.repo.ui = repoui
            
        return hgserve
