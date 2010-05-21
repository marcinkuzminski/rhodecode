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

from mercurial.hgweb import hgweb
from mercurial.hgweb.request import wsgiapplication
from paste.auth.basic import AuthBasicAuthenticator
from paste.httpheaders import REMOTE_USER, AUTH_TYPE
from pylons_app.lib.utils import is_mercurial
from pylons_app.lib.auth import authfunc
from pylons_app.lib.utils import make_ui, invalidate_cache
from webob.exc import HTTPNotFound
import os

class SimpleHg(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        #authenticate this mercurial request using 
        realm = '%s %s' % (config['repos_name'], 'mercurial repository')
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
                app = wsgiapplication(self._make_app)
            except Exception as e:
                return HTTPNotFound()(environ, start_response)
            
            """we know that some change was made to repositories and we should
            invalidate the cache to see the changes right away"""
            invalidate_cache('full_changelog', repo_name)
            return app(environ, start_response)            

    def _make_app(self):
        hgserve = hgweb(self.repo_path)
        return  self.load_web_settings(hgserve)
        
                
    def load_web_settings(self, hgserve):
        repoui = make_ui(os.path.join(self.repo_path, '.hg', 'hgrc'), False)
        #set the global ui for hgserve
        hgserve.repo.ui = self.baseui
        
        if repoui:
            #set the repository based config
            hgserve.repo.ui = repoui
            
        return hgserve


