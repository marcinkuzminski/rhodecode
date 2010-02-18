import logging
from paste.urlparser import PkgResourcesParser
from pylons import request, tmpl_context as c
from pylons.controllers.util import forward
from pylons.i18n.translation import _
from pylons_app.lib.base import BaseController, render
import cgi

log = logging.getLogger(__name__)
class ErrorController(BaseController):
    """
    Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.
    """

    def document(self):

        resp = request.environ.get('pylons.original_response')
        c.error_message = cgi.escape(request.GET.get('code', str(resp.status)))
        c.error_explanation = self.get_error_explanation(resp.status_int)

        c.serv_p = ''.join(['http://', request.environ.get('HTTP_HOST', '')])

        #redirect to when error with given seconds
        c.redirect_time = 5
        c.redirect_module = _('Home page')# name to what your going to be redirected
        c.url_redirect = "/"

        return render('/errors/error_document.html')

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))

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


