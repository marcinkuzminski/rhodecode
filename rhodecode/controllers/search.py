# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.search
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Search controller for rhodecode

    :created_on: Aug 7, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import traceback

from pylons.i18n.translation import _
from pylons import request, config, tmpl_context as c

from rhodecode.lib.auth import LoginRequired
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.indexers import SCHEMA, IDX_NAME, ResultWrapper

from webhelpers.paginate import Page
from webhelpers.util import update_params

from whoosh.index import open_dir, EmptyIndexError
from whoosh.qparser import QueryParser, QueryParserError
from whoosh.query import Phrase, Wildcard, Term, Prefix

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
        c.cur_search = search_type = {'content': 'content',
                                      'commit': 'content',
                                      'path': 'path',
                                      'repository': 'repository'}\
                                      .get(c.cur_type, 'content')

        if c.cur_query:
            cur_query = c.cur_query.lower()

        if c.cur_query:
            p = int(request.params.get('page', 1))
            highlight_items = set()
            try:
                idx = open_dir(config['app_conf']['index_dir'],
                               indexname=IDX_NAME)
                searcher = idx.searcher()

                qp = QueryParser(search_type, schema=SCHEMA)
                if c.repo_name:
                    cur_query = u'repository:%s %s' % (c.repo_name, cur_query)
                try:
                    query = qp.parse(unicode(cur_query))
                    # extract words for highlight
                    if isinstance(query, Phrase):
                        highlight_items.update(query.words)
                    elif isinstance(query, Prefix):
                        highlight_items.add(query.text)
                    else:
                        for i in query.all_terms():
                            if i[0] == 'content':
                                highlight_items.add(i[1])

                    matcher = query.matcher(searcher)

                    log.debug(query)
                    log.debug(highlight_items)
                    results = searcher.search(query)
                    res_ln = len(results)
                    c.runtime = '%s results (%.3f seconds)' % (
                        res_ln, results.runtime
                    )

                    def url_generator(**kw):
                        return update_params("?q=%s&type=%s" \
                                           % (c.cur_query, c.cur_search), **kw)

                    c.formated_results = Page(
                        ResultWrapper(search_type, searcher, matcher,
                                      highlight_items),
                        page=p,
                        item_count=res_ln,
                        items_per_page=10,
                        url=url_generator
                    )

                except QueryParserError:
                    c.runtime = _('Invalid search query. Try quoting it.')
                searcher.close()
            except (EmptyIndexError, IOError):
                log.error(traceback.format_exc())
                log.error('Empty Index data')
                c.runtime = _('There is no index to search in. '
                              'Please run whoosh indexer')
            except (Exception):
                log.error(traceback.format_exc())
                c.runtime = _('An error occurred during this search operation')


        # Return a rendered template
        return render('/search/search.html')
