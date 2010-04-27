import os

import cgi
from mercurial import util
from mercurial.hgweb.request import wsgirequest, normalize
from mercurial.hgweb import hgweb
from pylons.controllers.util import Response
from mercurial.hgweb.request import wsgiapplication


class SimpleHg(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        
    def __call__(self, environ, start_response):
        if not is_mercurial(environ):
            return self.application(environ, start_response)
        else:
            from pprint import pprint
            pprint(environ)

            repo_path = os.path.join('/home/marcink/python_workspace/', environ['PATH_INFO'].replace('/', ''))
            def _make_app():return hgweb(repo_path, "Name")
            app = wsgiapplication(_make_app)
            return app(environ, start_response)            
                
def is_mercurial(environ):
    """
    Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    http_accept = environ.get('HTTP_ACCEPT')
    if http_accept and http_accept.startswith('application/mercurial'):
        return True
    return False
