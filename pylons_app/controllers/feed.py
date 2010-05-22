#!/usr/bin/python
# -*- coding: utf-8 -*-
import logging
from operator import itemgetter
from pylons import tmpl_context as c, request, config
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.utils import get_repo_slug
from pylons_app.model.hg_model import HgModel
from pylons_app.lib.auth import LoginRequired
log = logging.getLogger(__name__)

class FeedController(BaseController):
    
    #secure it or not ?
    def __before__(self):
        super(FeedController, self).__before__()
        
    def atom(self):
        return 'Hello Atom'
    
    def rss(self):
        return 'Hello rss'
