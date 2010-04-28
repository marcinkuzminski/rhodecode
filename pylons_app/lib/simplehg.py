import os
from mercurial.hgweb import hgweb
from mercurial.hgweb.request import wsgiapplication
from pylons_app.lib.utils import make_ui
class SimpleHg(object):

    def __init__(self, application, config):
        self.application = application
        self.config = config
        
    def __call__(self, environ, start_response):
        if not is_mercurial(environ):
            return self.application(environ, start_response)
        else:
            repo_name = environ['PATH_INFO'].replace('/', '')
            if not environ['PATH_INFO'].endswith == '/':
                environ['PATH_INFO'] += '/'
            #environ['SCRIPT_NAME'] = request.path
            environ['PATH_INFO'] = '/'
            self.baseui = make_ui()
            self.basepath = self.baseui.configitems('paths')[0][1].replace('*', '')
            self.repo_path = os.path.join(self.basepath, repo_name)
            app = wsgiapplication(self._make_app)
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
                                
def is_mercurial(environ):
    """
    Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    http_accept = environ.get('HTTP_ACCEPT')
    if http_accept and http_accept.startswith('application/mercurial'):
        return True
    return False


