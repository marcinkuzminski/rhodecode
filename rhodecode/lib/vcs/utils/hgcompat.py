"""
Mercurial libs compatibility
"""

import mercurial
import mercurial.demandimport
## patch demandimport, due to bug in mercurial when it allways triggers demandimport.enable()
mercurial.demandimport.enable = lambda *args, **kwargs: 1
from mercurial import archival, merge as hg_merge, patch, ui
from mercurial import discovery
from mercurial import localrepo
from mercurial import unionrepo
from mercurial import scmutil
from mercurial import config
from mercurial.commands import clone, nullid, pull
from mercurial.context import memctx, memfilectx
from mercurial.error import RepoError, RepoLookupError, Abort
from mercurial.hgweb import hgweb_mod
from mercurial.hgweb.common import get_contact
from mercurial.localrepo import localrepository
from mercurial.match import match
from mercurial.mdiff import diffopts
from mercurial.node import hex
from mercurial.encoding import tolocal
from mercurial.discovery import findcommonoutgoing
from mercurial.hg import peer
from mercurial.httppeer import httppeer
from mercurial.util import url as hg_url
from mercurial.scmutil import revrange
from mercurial.node import nullrev

# those authnadlers are patched for python 2.6.5 bug an
# infinit looping when given invalid resources
from mercurial.url import httpbasicauthhandler, httpdigestauthhandler
