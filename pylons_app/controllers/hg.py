#!/usr/bin/python
# -*- coding: utf-8 -*-
from mako.template import Template
from mercurial.hg import repository
from mercurial.hgweb import hgweb
from mercurial.hgweb.request import wsgiapplication
from mercurial.localrepo import localrepository
from operator import itemgetter
from pylons import tmpl_context as c, app_globals as g, session, request, config
from pylons.controllers.util import abort
from pylons_app.lib import helpers as h
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
import logging
import os
from beaker.cache import cache_region
log = logging.getLogger(__name__)

class HgController(BaseController):

    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.staticurl = g.statics
        c.repo_name = get_repo_slug(request)
        
    def index(self):
        

        hg_model = HgModel()
        @cache_region('short_term', 'repo_list')
        def _list():
            return list(hg_model.get_repos())
        
        c.repos_list = _list()
        c.current_sort = request.GET.get('sort', 'name')
        
        cs = c.current_sort
        c.cs_slug = cs.replace('-', '')
        sortables = ['name', 'description', 'last_change', 'tip', 'contact']
        
        if cs and c.cs_slug in sortables:
            sort_key = c.cs_slug + '_sort'
            if cs.startswith('-'):
                c.repos_list.sort(key=itemgetter(sort_key), reverse=True)
            else:
                c.repos_list.sort(key=itemgetter(sort_key), reverse=False)
            
        return render('/index.html')

    def view(self, environ, start_response, path_info):
        print path_info
        
        def app_maker():           
            
            path = os.path.join(g.base_path, c.repo_name)
            repo = repository(g.baseui, path)
            hgwebapp = hgweb(repo, c.repo_name)
            return hgwebapp
        
        a = wsgiapplication(app_maker)
        resp = a(environ, start_response)

        http_accept = request.environ.get('HTTP_ACCEPT', False)
        if not http_accept:
            return abort(status_code=400, detail='no http accept in header')
        
        #for mercurial protocols and raw files we can't wrap into mako
        if http_accept.find("mercurial") != -1 or \
        request.environ['PATH_INFO'].find('raw-file') != -1:
                    return resp
        try:
            tmpl = u''.join(resp)
            template = Template(tmpl, lookup=request.environ['pylons.pylons']\
                            .config['pylons.app_globals'].mako_lookup)
                        
        except (RuntimeError, UnicodeDecodeError):
            log.info('disabling unicode due to encoding error')
            resp = g.hgapp(request.environ, self.start_response)
            tmpl = ''.join(resp)
            template = Template(tmpl, lookup=request.environ['pylons.pylons']\
                            .config['pylons.app_globals'].mako_lookup, disable_unicode=True)

        return template.render(g=g, c=c, session=session, h=h)
