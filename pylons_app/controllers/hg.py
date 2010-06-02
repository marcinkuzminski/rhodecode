#!/usr/bin/python
# -*- coding: utf-8 -*-
from operator import itemgetter
from pylons import tmpl_context as c, request, config
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.model.hg_model import HgModel
import logging
log = logging.getLogger(__name__)

class HgController(BaseController):

    @LoginRequired()
    def __before__(self):
        super(HgController, self).__before__()
        
    def index(self):
        c.current_sort = request.GET.get('sort', 'name')
        cs = c.current_sort
        c.cs_slug = cs.replace('-', '')
        sortables = ['name', 'description', 'last_change', 'tip', 'contact']
        cached_repo_list = HgModel().get_repos()
        if cs and c.cs_slug in sortables:
            sort_key = c.cs_slug + '_sort'
            if cs.startswith('-'):
                c.repos_list = sorted(cached_repo_list, key=itemgetter(sort_key), reverse=True)
            else:
                c.repos_list = sorted(cached_repo_list, key=itemgetter(sort_key), reverse=False)
            
        return render('/index.html')
