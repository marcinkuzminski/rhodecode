import logging
import cgi
import os
import paste.fileapp
from pylons import tmpl_context as c, app_globals as g, request, config
from pylons.controllers.util import forward
from pylons.i18n.translation import _
from rhodecode.lib.base import BaseController, render
from pylons.middleware import  media_path
from rhodecode.lib.utils import check_repo
import rhodecode.lib.helpers as h
from rhodecode import __version__
log = logging.getLogger(__name__)

class ErrorController(BaseController):
    """
    Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.
    """
    def __before__(self):
        pass#disable all base actions since we don't need them here
        
    def document(self):
        resp = request.environ.get('pylons.original_response')
        
        log.debug('### %s ###', resp.status)

        e = request.environ
        c.serv_p = r'%(protocol)s://%(host)s/' % {
                                                'protocol': e.get('wsgi.url_scheme'),
                                                'host':e.get('HTTP_HOST'),
                                                }

                
        c.error_message = cgi.escape(request.GET.get('code', str(resp.status)))
        c.error_explanation = self.get_error_explanation(resp.status_int)

        #redirect to when error with given seconds
        c.redirect_time = 0
        c.redirect_module = _('Home page')# name to what your going to be redirected
        c.url_redirect = "/"

        return render('/errors/error_document.html')


    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file(os.path.join(media_path, 'img', id))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file(os.path.join(media_path, 'style', id))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        fapp = paste.fileapp.FileApp(path)
        return fapp(request.environ, self.start_response)

    def get_error_explanation(self, code):
        ''' get the error explanations of int codes
            [400, 401, 403, 404, 500]'''
        try:
            code = int(code)
        except:
            code = 500

        if code == 400:
            return _('The request could not be understood by the server due to malformed syntax.')
        if code == 401:
            return _('Unathorized access to resource')
        if code == 403:
            return _("You don't have permission to view this page")
        if code == 404:
            return _('The resource could not be found')
        if code == 500:
            return _('The server encountered an unexpected condition which prevented it from fulfilling the request.')


