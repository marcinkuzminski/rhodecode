#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from pylons import tmpl_context as c, app_globals as g, session, request, config
from pylons_app.lib import helpers as h
from pylons_app.lib.base import BaseController, render
from mako.template import Template
from pylons.controllers.util import abort

from operator import itemgetter
from pylons_app.model.hg_model import HgModel
log = logging.getLogger(__name__)

class HgController(BaseController):

    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.staticurl = g.statics

    def index(self):
        hg_model = HgModel()
        c.repos_list = list(hg_model.get_repos())
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

    def view(self, *args, **kwargs):
        #TODO: reimplement this not tu use hgwebdir
        
        vcs_impl = self._get_vcs_impl(request.environ) 
        if vcs_impl:
            return vcs_impl
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
    
    
    
    
    def _get_vcs_impl(self, environ):
        path_info = environ['PATH_INFO']
        c.repo_name = path_info.split('/')[-2]
        action = path_info.split('/')[-1]
        if not action.startswith('_'):
            return False
        else:
            hg_model = HgModel()
            c.repo_info = hg_model.get_repo(c.repo_name)
            c.repo_changesets = c.repo_info.get_changesets(10)
            return render('/summary.html')
