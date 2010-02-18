#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from pylons_app.lib.base import BaseController
from pylons import c, g, session, h, request
from mako.template import Template
from pprint import pprint
#uncomment the following if you want to serve a single repo
#from mercurial.hgweb.hgweb_mod import hgweb
from mercurial.hgweb.hgwebdir_mod import hgwebdir
from mercurial.hgweb.request import wsgiapplication
log = logging.getLogger(__name__)

#http://bel-epa.com/hg/
#def make_web_app():
#    repos = "hgwebdir.config"
#    hgwebapp = hgwebdir(repos)
#    return hgwebapp
#
#class HgController(BaseController):
#
#    def index(self):
#        hgapp = wsgiapplication(make_web_app)
#        return hgapp(request.environ, self.start_response)
#
#    def view(self, *args, **kwargs):
#        return u'dupa'
#        #pprint(request.environ)
#        hgapp = wsgiapplication(make_web_app)
#        return hgapp(request.environ, self.start_response)

def _make_app():
    #for single a repo
    #return hgweb("/path/to/repo", "Name")
    repos = "hgwebdir.config"
    return  hgwebdir(repos)

def wsgi_app(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/html')])
    return ['<html>\n<body>\nHello World!\n</body>\n</html>']

class HgController(BaseController):



    def view(self, environ, start_response):
        #the following is only needed when using hgwebdir
        app = _make_app()
        #return wsgi_app(environ, start_response)
        response = app(request.environ, self.start_response)

        if environ['PATH_INFO'].find("static") != -1:
            return response
        else:
            #wrap the murcurial response in a mako template.
            template = Template("".join(response),
                                lookup = environ['pylons.pylons']\
                                .config['pylons.g'].mako_lookup)

            return template.render(g = g, c = c, session = session, h = h)

