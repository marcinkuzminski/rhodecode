import sys
import os
from pidlock import LockHeld, DaemonLock
import traceback

from os.path import dirname as dn
from os.path import join as jn

#to get the pylons_app import
sys.path.append(dn(dn(dn(os.path.realpath(__file__)))))

from pylons_app.config.environment import load_environment
from pylons_app.model.hg_model import HgModel
from whoosh.analysis import RegexTokenizer, LowercaseFilter, StopFilter
from whoosh.fields import TEXT, ID, STORED, Schema
from whoosh.index import create_in, open_dir
from shutil import rmtree

#LOCATION WE KEEP THE INDEX
IDX_LOCATION = jn(dn(dn(dn(dn(os.path.abspath(__file__))))), 'data', 'index')

#EXTENSION TO SKIP READING CONTENT ON
EXCLUDE_EXTENSIONS = ['pyc', 'mo', 'png', 'jpg', 'jpeg', 'gif', 'swf',
                       'dll', 'ttf', 'psd', 'svg', 'pdf', 'bmp', 'dll']

#CUSTOM ANALYZER wordsplit + lowercase filter
ANALYZER = RegexTokenizer() | LowercaseFilter()

#INDEX SCHEMA DEFINITION
SCHEMA = Schema(owner=TEXT(),
                repository=TEXT(stored=True),
                path=ID(stored=True, unique=True),
                content=TEXT(stored=True, analyzer=ANALYZER),
                modtime=STORED())

IDX_NAME = 'HG_INDEX'
