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
from pylons import request, response, config, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from rhodecode.lib.auth import LoginRequired
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.indexers import SCHEMA, IDX_NAME, ResultWrapper
from webhelpers.paginate import Page
from webhelpers.util import update_params
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

    def index(self, search_repo=None):
        c.repo_name = search_repo
        c.formated_results = []
        c.runtime = ''
        c.cur_query = request.GET.get('q', None)
        c.cur_type = request.GET.get('type', 'source')
        c.cur_search = search_type = {'content':'content',
                                      'commit':'content',
                                      'path':'path',
                                      'repository':'repository'}\
                                      .get(c.cur_type, 'content')


        if c.cur_query:
            cur_query = c.cur_query.lower()

        if c.cur_query:
            p = int(request.params.get('page', 1))
            highlight_items = set()
            try:
                idx = open_dir(config['app_conf']['index_dir']
                               , indexname=IDX_NAME)
                searcher = idx.searcher()

                qp = QueryParser(search_type, schema=SCHEMA)
                if c.repo_name:
                    cur_query = u'repository:%s %s' % (c.repo_name, cur_query)
                try:
                    query = qp.parse(unicode(cur_query))

                    if isinstance(query, Phrase):
                        highlight_items.update(query.words)
                    else:
                        for i in query.all_terms():
                            if i[0] == 'content':
                                highlight_items.add(i[1])

                    matcher = query.matcher(searcher)

                    log.debug(query)
                    log.debug(highlight_items)
                    results = searcher.search(query)
                    res_ln = len(results)
                    c.runtime = '%s results (%.3f seconds)' \
                        % (res_ln, results.runtime)

                    def url_generator(**kw):
                        return update_params("?q=%s&type=%s" \
                                           % (c.cur_query, c.cur_search), **kw)

                    c.formated_results = Page(
                                ResultWrapper(search_type, searcher, matcher,
                                              highlight_items),
                                page=p, item_count=res_ln,
                                items_per_page=10, url=url_generator)


                except QueryParserError:
                    c.runtime = _('Invalid search query. Try quoting it.')
                searcher.close()
            except (EmptyIndexError, IOError):
                log.error(traceback.format_exc())
                log.error('Empty Index data')
                c.runtime = _('There is no index to search in. Please run whoosh indexer')

        # Return a rendered template
        return render('/search/search.html')
