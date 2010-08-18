#!/usr/bin/env python
# encoding: utf-8
# search controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
"""
Created on Aug 7, 2010
search controller for pylons
@author: marcink
"""
from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons_app.lib.auth import LoginRequired
from pylons_app.lib.base import BaseController, render
from pylons_app.lib.indexers import ANALYZER, IDX_LOCATION, SCHEMA, IDX_NAME
from webhelpers.html.builder import escape
from whoosh.highlight import highlight, SimpleFragmenter, HtmlFormatter, \
    ContextFragmenter
from pylons.i18n.translation import _
from whoosh.index import open_dir, EmptyIndexError
from whoosh.qparser import QueryParser, QueryParserError
from whoosh.query import Phrase
import logging
import traceback

log = logging.getLogger(__name__)

class SearchController(BaseController):

    @LoginRequired()
    def __before__(self):
        super(SearchController, self).__before__()    


    def index(self):
        c.formated_results = []
        c.runtime = ''
        search_items = set()
        c.cur_query = request.GET.get('q', None)
        if c.cur_query:
            cur_query = c.cur_query.lower()
        
        
        if c.cur_query:
            try:
                idx = open_dir(IDX_LOCATION, indexname=IDX_NAME)
                searcher = idx.searcher()
            
                qp = QueryParser("content", schema=SCHEMA)
                try:
                    query = qp.parse(unicode(cur_query))
                    
                    if isinstance(query, Phrase):
                        search_items.update(query.words)
                    else:
                        for i in query.all_terms():
                            search_items.add(i[1])
                        
                    log.debug(query)
                    log.debug(search_items)
                    results = searcher.search(query)
                    c.runtime = '%s results (%.3f seconds)' \
                    % (len(results), results.runtime)

                    analyzer = ANALYZER
                    formatter = HtmlFormatter('span',
                        between='\n<span class="break">...</span>\n') 
                    
                    #how the parts are splitted within the same text part
                    fragmenter = SimpleFragmenter(200)
                    #fragmenter = ContextFragmenter(search_items)
                    
                    for res in results:
                        d = {}
                        d.update(res)
                        hl = highlight(escape(res['content']), search_items,
                                                         analyzer=analyzer,
                                                         fragmenter=fragmenter,
                                                         formatter=formatter,
                                                         top=5)
                        f_path = res['path'][res['path'].find(res['repository']) \
                                             + len(res['repository']):].lstrip('/')
                        d.update({'content_short':hl,
                                  'f_path':f_path})
                        #del d['content']
                        c.formated_results.append(d)
                                                    
                except QueryParserError:
                    c.runtime = _('Invalid search query. Try quoting it.')

            except (EmptyIndexError, IOError):
                log.error(traceback.format_exc())
                log.error('Empty Index data')
                c.runtime = _('There is no index to search in. Please run whoosh indexer')
            

                
        # Return a rendered template
        return render('/search/search.html')
