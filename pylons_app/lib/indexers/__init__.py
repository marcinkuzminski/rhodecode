from os.path import dirname as dn, join as jn
from pidlock import LockHeld, DaemonLock
from pylons_app.config.environment import load_environment
from pylons_app.model.hg_model import HgModel
from shutil import rmtree
from webhelpers.html.builder import escape
from vcs.utils.lazy import LazyProperty

from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter
from whoosh.fields import TEXT, ID, STORED, Schema, FieldType
from whoosh.index import create_in, open_dir
from whoosh.formats import Characters
from whoosh.highlight import highlight, SimpleFragmenter, HtmlFormatter   

import os
import sys
import traceback



#to get the pylons_app import
sys.path.append(dn(dn(dn(os.path.realpath(__file__)))))


#LOCATION WE KEEP THE INDEX
IDX_LOCATION = jn(dn(dn(dn(dn(os.path.abspath(__file__))))), 'data', 'index')

#EXTENSIONS WE WANT TO INDEX CONTENT OFF
INDEX_EXTENSIONS = ['action', 'adp', 'ashx', 'asmx', 'aspx', 'asx', 'axd', 'c',
                    'cfg', 'cfm', 'cpp', 'cs', 'css', 'diff', 'do', 'el', 'erl',
                    'h', 'htm', 'html', 'ini', 'java', 'js', 'jsp', 'jspx', 'lisp',
                    'lua', 'm', 'mako', 'ml', 'pas', 'patch', 'php', 'php3',
                    'php4', 'phtml', 'pm', 'py', 'rb', 'rst', 's', 'sh', 'sql',
                    'tpl', 'txt', 'vim', 'wss', 'xhtml', 'xml', 'xsl', 'xslt',
                    'yaws']

#CUSTOM ANALYZER wordsplit + lowercase filter
ANALYZER = RegexTokenizer(expression=r"\w+") | LowercaseFilter()


#INDEX SCHEMA DEFINITION
SCHEMA = Schema(owner=TEXT(),
                repository=TEXT(stored=True),
                path=ID(stored=True, unique=True),
                content=FieldType(format=Characters(ANALYZER),
                             scorable=True, stored=True),
                modtime=STORED(), extension=TEXT(stored=True))


IDX_NAME = 'HG_INDEX'
FORMATTER = HtmlFormatter('span', between='\n<span class="break">...</span>\n') 
FRAGMENTER = SimpleFragmenter(200)
                 
                    

                            
class ResultWrapper(object):
    def __init__(self, searcher, matcher, highlight_items):
        self.searcher = searcher
        self.matcher = matcher
        self.highlight_items = highlight_items
        self.fragment_size = 150 * 2
    
    @LazyProperty
    def doc_ids(self):
        docs_id = []
        while self.matcher.is_active():
            docnum = self.matcher.id()
            docs_id.append(docnum)
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

    def __getslice__(self, i, j):
        """
        Slicing of resultWrapper
        """
        slice = []
        for docid in self.doc_ids[i:j]:
            slice.append(self.get_full_content(docid))
        return slice   
                            

    def get_full_content(self, docid):
        res = self.searcher.stored_fields(docid)
        f_path = res['path'][res['path'].find(res['repository']) \
                             + len(res['repository']):].lstrip('/')
        
        content_short = ''.join(self.get_short_content(res))
        res.update({'content_short':content_short,
                    'content_short_hl':self.highlight(content_short),
                    'f_path':f_path})
        
        return res        

    def get_short_content(self, res):
        """
        Smart function that implements chunking the content
        but not overlap chunks so it doesn't highlight the same
        close occurences twice.
        @param matcher:
        @param size:
        """
        memory = [(0, 0)]
        for span in self.matcher.spans():
            start = span.startchar or 0
            end = span.endchar or 0
            start_offseted = max(0, start - self.fragment_size)
            end_offseted = end + self.fragment_size
            print start_offseted, end_offseted
            if start_offseted < memory[-1][1]:
                start_offseted = memory[-1][1]
            memory.append((start_offseted, end_offseted,))    
            yield res["content"][start_offseted:end_offseted]  
        
    def highlight(self, content, top=5):
        hl = highlight(escape(content),
                 self.highlight_items,
                 analyzer=ANALYZER,
                 fragmenter=FRAGMENTER,
                 formatter=FORMATTER,
                 top=top)
        return hl 
