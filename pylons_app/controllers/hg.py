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
