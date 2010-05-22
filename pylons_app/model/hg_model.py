#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 marcink.  All rights reserved.
#
from vcs.exceptions import RepositoryError
'''
Created on Apr 9, 2010

@author: marcink
'''
import os
from pylons import tmpl_context as c, app_globals as g, session, request, config
from pylons.controllers.util import abort
import sys
try:
    from vcs.backends.hg import get_repositories, MercurialRepository
except ImportError:
    sys.stderr.write('You have to import vcs module')
    raise Exception('Unable to import vcs')

class HgModel(object):
    """
    Mercurial Model
    """


    def __init__(self):
        """
        Constructor
        """
        pass

    def get_repos(self):
        for mercurial_repo in get_repositories(g.paths[0][0], g.paths[0][1], g.baseui):
            
            if mercurial_repo._get_hidden():
                #skip hidden web repository
                continue
            
            last_change = mercurial_repo.last_change
            try:
                tip = mercurial_repo.get_changeset('tip')
            except RepositoryError:
                from pylons_app.lib.utils import EmptyChangeset
                tip = EmptyChangeset()
                
            tmp_d = {}
            tmp_d['name'] = mercurial_repo.name
            tmp_d['name_sort'] = tmp_d['name']
            tmp_d['description'] = mercurial_repo.description
            tmp_d['description_sort'] = tmp_d['description']
            tmp_d['last_change'] = last_change
            tmp_d['last_change_sort'] = last_change[1] - last_change[0]
            tmp_d['tip'] = tip.raw_id
            tmp_d['tip_sort'] = tip.revision 
            tmp_d['rev'] = tip.revision
            tmp_d['contact'] = mercurial_repo.contact
            tmp_d['contact_sort'] = tmp_d['contact']
            tmp_d['repo_archives'] = list(mercurial_repo._get_archives())
            
            yield tmp_d

    def get_repo(self, repo_name):
        path = g.paths[0][1].replace('*', '')
        repo = MercurialRepository(os.path.join(path, repo_name), baseui=g.baseui)
        return repo
