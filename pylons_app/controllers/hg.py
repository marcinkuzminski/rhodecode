#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from pylons_app.lib.base import BaseController
from pylons import tmpl_context as c, app_globals as g, session, request, config
from pylons_app.lib import helpers as h
from mako.template import Template
from pylons.controllers.util import abort

log = logging.getLogger(__name__)

class HgController(BaseController):

    def __before__(self):
        c.repos_prefix = config['repos_name']

    def view(self, *args, **kwargs):
        response = g.hgapp(request.environ, self.start_response)
        
        http_accept = request.environ.get('HTTP_ACCEPT', False)
        if not http_accept:
            return abort(status_code=400, detail='no http accept in header')
        
        #for mercurial protocols and raw files we can't wrap into mako
        if http_accept.find("mercurial") != -1 or \
        request.environ['PATH_INFO'].find('raw-file') != -1:
                    return response
        try:
            tmpl = u''.join(response)
            template = Template(tmpl, lookup=request.environ['pylons.pylons']\
                            .config['pylons.app_globals'].mako_lookup)
                        
        except (RuntimeError, UnicodeDecodeError):
            log.info('disabling unicode due to encoding error')
            response = g.hgapp(request.environ, self.start_response)
            tmpl = ''.join(response)
            template = Template(tmpl, lookup=request.environ['pylons.pylons']\
                            .config['pylons.app_globals'].mako_lookup, disable_unicode=True)


        return template.render(g=g, c=c, session=session, h=h)
