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
    from vcs.backends.hg import get_repositories, MercurialRepository
except ImportError:
    print 'You have to import vcs module'
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
            tip_rev = mercurial_repo._get_revision('tip')
            tip = mercurial_repo.get_changeset(tip_rev)
            tmp_d = {}
            tmp_d['name'] = mercurial_repo.name
            tmp_d['name_sort'] = tmp_d['name']
            tmp_d['description'] = mercurial_repo.description
            tmp_d['description_sort'] = tmp_d['description']
            tmp_d['last_change'] = last_change
            tmp_d['last_change_sort'] = last_change[1] - last_change[0]
            tmp_d['tip'] = tip._short
            tmp_d['tip_sort'] = tip_rev
            tmp_d['rev'] = tip_rev
            tmp_d['contact'] = mercurial_repo.contact
            tmp_d['contact_sort'] = tmp_d['contact']
            tmp_d['repo_archives'] = list(mercurial_repo._get_archives())
            
            yield tmp_d

    def get_repo(self, repo_name):
        path = g.paths[0][1].replace('*', '')
        repo = MercurialRepository(os.path.join(path, repo_name), baseui=g.baseui)
        return repo
