# -*- coding: utf-8 -*-
"""
    rhodecode.lib.indexers.__init__
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Whoosh indexing module for RhodeCode

    :created_on: Aug 17, 2010
    :author: marcink
    :copyright: (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
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
import os
import sys
import traceback
from os.path import dirname as dn, join as jn

#to get the rhodecode import
sys.path.append(dn(dn(dn(os.path.realpath(__file__)))))

from string import strip
from shutil import rmtree

from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter
from whoosh.fields import TEXT, ID, STORED, Schema, FieldType
from whoosh.index import create_in, open_dir
from whoosh.formats import Characters
from whoosh.highlight import highlight, SimpleFragmenter, HtmlFormatter

from webhelpers.html.builder import escape
from sqlalchemy import engine_from_config
from vcs.utils.lazy import LazyProperty

from rhodecode.model import init_model
from rhodecode.model.scm import ScmModel
from rhodecode.model.repo import RepoModel
from rhodecode.config.environment import load_environment
from rhodecode.lib import LANGUAGES_EXTENSIONS_MAP
from rhodecode.lib.utils import BasePasterCommand, Command, add_cache

#EXTENSIONS WE WANT TO INDEX CONTENT OFF
INDEX_EXTENSIONS = LANGUAGES_EXTENSIONS_MAP.keys()

#CUSTOM ANALYZER wordsplit + lowercase filter
ANALYZER = RegexTokenizer(expression=r"\w+") | LowercaseFilter()


#INDEX SCHEMA DEFINITION
SCHEMA = Schema(owner=TEXT(),
                repository=TEXT(stored=True),
                path=TEXT(stored=True),
                content=FieldType(format=Characters(ANALYZER),
                             scorable=True, stored=True),
                modtime=STORED(), extension=TEXT(stored=True))


IDX_NAME = 'HG_INDEX'
FORMATTER = HtmlFormatter('span', between='\n<span class="break">...</span>\n')
FRAGMENTER = SimpleFragmenter(200)


class MakeIndex(BasePasterCommand):

    max_args = 1
    min_args = 1

    usage = "CONFIG_FILE"
    summary = "Creates index for full text search given configuration file"
    group_name = "RhodeCode"
    takes_config_file = -1
    parser = Command.standard_parser(verbose=True)

    def command(self):

        from pylons import config
        add_cache(config)
        engine = engine_from_config(config, 'sqlalchemy.db1.')
        init_model(engine)

        index_location = config['index_dir']
        repo_location = self.options.repo_location \
            if self.options.repo_location else RepoModel().repos_path
        repo_list = map(strip, self.options.repo_list.split(',')) \
            if self.options.repo_list else None

        #======================================================================
        # WHOOSH DAEMON
        #======================================================================
        from rhodecode.lib.pidlock import LockHeld, DaemonLock
        from rhodecode.lib.indexers.daemon import WhooshIndexingDaemon
        try:
            l = DaemonLock(file_=jn(dn(dn(index_location)), 'make_index.lock'))
            WhooshIndexingDaemon(index_location=index_location,
                                 repo_location=repo_location,
                                 repo_list=repo_list)\
                .run(full_index=self.options.full_index)
            l.release()
        except LockHeld:
            sys.exit(1)

    def update_parser(self):
        self.parser.add_option('--repo-location',
                          action='store',
                          dest='repo_location',
                          help="Specifies repositories location to index OPTIONAL",
                          )
        self.parser.add_option('--index-only',
                          action='store',
                          dest='repo_list',
                          help="Specifies a comma separated list of repositores "
                                "to build index on OPTIONAL",
                          )
        self.parser.add_option('-f',
                          action='store_true',
                          dest='full_index',
                          help="Specifies that index should be made full i.e"
                                " destroy old and build from scratch",
                          default=False)

class ResultWrapper(object):
    def __init__(self, search_type, searcher, matcher, highlight_items):
        self.search_type = search_type
        self.searcher = searcher
        self.matcher = matcher
        self.highlight_items = highlight_items
        self.fragment_size = 200 / 2

    @LazyProperty
    def doc_ids(self):
        docs_id = []
        while self.matcher.is_active():
            docnum = self.matcher.id()
            chunks = [offsets for offsets in self.get_chunks()]
            docs_id.append([docnum, chunks])
            self.matcher.next()
        return docs_id

    def __str__(self):
        return '<%s at %s>' % (self.__class__.__name__, len(self.doc_ids))

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.doc_ids)

    def __iter__(self):
        """
        Allows Iteration over results,and lazy generate content

        *Requires* implementation of ``__getitem__`` method.
        """
        for docid in self.doc_ids:
            yield self.get_full_content(docid)

    def __getitem__(self, key):
        """
        Slicing of resultWrapper
        """
        i, j = key.start, key.stop

        slice = []
        for docid in self.doc_ids[i:j]:
            slice.append(self.get_full_content(docid))
        return slice


    def get_full_content(self, docid):
        res = self.searcher.stored_fields(docid[0])
        f_path = res['path'][res['path'].find(res['repository']) \
                             + len(res['repository']):].lstrip('/')

        content_short = self.get_short_content(res, docid[1])
        res.update({'content_short':content_short,
                    'content_short_hl':self.highlight(content_short),
                    'f_path':f_path})

        return res

    def get_short_content(self, res, chunks):

        return ''.join([res['content'][chunk[0]:chunk[1]] for chunk in chunks])

    def get_chunks(self):
        """
        Smart function that implements chunking the content
        but not overlap chunks so it doesn't highlight the same
        close occurrences twice.
        
        :param matcher:
        :param size:
        """
        memory = [(0, 0)]
        for span in self.matcher.spans():
            start = span.startchar or 0
            end = span.endchar or 0
            start_offseted = max(0, start - self.fragment_size)
            end_offseted = end + self.fragment_size

            if start_offseted < memory[-1][1]:
                start_offseted = memory[-1][1]
            memory.append((start_offseted, end_offseted,))
            yield (start_offseted, end_offseted,)

    def highlight(self, content, top=5):
        if self.search_type != 'content':
            return ''
        hl = highlight(escape(content),
                 self.highlight_items,
                 analyzer=ANALYZER,
                 fragmenter=FRAGMENTER,
                 formatter=FORMATTER,
                 top=top)
        return hl
