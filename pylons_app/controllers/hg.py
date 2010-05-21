#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from operator import itemgetter
from pylons import tmpl_context as c, request, config
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
log = logging.getLogger(__name__)

class HgController(BaseController):

    def __before__(self):
        c.repos_prefix = config['repos_name']
        c.repo_name = get_repo_slug(request)
        
    def index(self):
        c.current_sort = request.GET.get('sort', 'name')
        cs = c.current_sort
        c.cs_slug = cs.replace('-', '')
        sortables = ['name', 'description', 'last_change', 'tip', 'contact']
        
        if cs and c.cs_slug in sortables:
            sort_key = c.cs_slug + '_sort'
            if cs.startswith('-'):
                c.repos_list = sorted(c.cached_repo_list, key=itemgetter(sort_key), reverse=True)
            else:
                c.repos_list = sorted(c.cached_repo_list, key=itemgetter(sort_key), reverse=False)
            
        return render('/index.html')
