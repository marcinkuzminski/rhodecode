#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 marcink.  All rights reserved.
#
'''
Created on Apr 9, 2010

@author: marcink
'''
import os
from pylons import tmpl_context as c, app_globals as g, session, request, config
from pylons.controllers.util import abort
try:
    from vcs.backends.hg import get_repositories
except ImportError:
    print 'You have to import vcs module'
from mercurial.util import matchdate, Abort, makedate
from mercurial.hgweb.common import get_contact
from mercurial.templatefilters import age

class HgModel(object):
    """
    Mercurial Model
    """


    def __init__(self):
        """
        Constructor
        """
        

    def get_mtime(self, spath):
        cl_path = os.path.join(spath, "00changelog.i")
        if os.path.exists(cl_path):
            return os.stat(cl_path).st_mtime
        else:
            return os.stat(spath).st_mtime   
    
    def archivelist(self, ui, nodeid, url):
        allowed = g.baseui.configlist("web", "allow_archive", untrusted=True)
        for i in [('zip', '.zip'), ('gz', '.tar.gz'), ('bz2', '.tar.bz2')]:
            if i[0] in allowed or ui.configbool("web", "allow" + i[0],
                                                untrusted=True):
                yield {"type" : i[0], "extension": i[1],
                       "node": nodeid, "url": url}

    def get_repos(self):
        for name, r in get_repositories(g.paths[0][0], g.paths[0][1]).items():
            last_change = (self.get_mtime(r.spath), makedate()[1])
            tip = r.changectx('tip')
            tmp_d = {}
            tmp_d['name'] = name
            tmp_d['name_sort'] = tmp_d['name']
            tmp_d['description'] = r.ui.config('web', 'description', 'Unknown', untrusted=True)
            tmp_d['description_sort'] = tmp_d['description']
            tmp_d['last_change'] = age(last_change)
            tmp_d['last_change_sort'] = last_change[1] - last_change[0]
            tmp_d['tip'] = str(tip)
            tmp_d['tip_sort'] = tip.rev()
            tmp_d['rev'] = tip.rev()
            tmp_d['contact'] = get_contact(r.ui.config) or 'unknown'
            tmp_d['contact_sort'] = get_contact(r.ui.config)
            tmp_d['repo_archives'] = self.archivelist(r.ui, "tip", 'sa')
            
            yield tmp_d
