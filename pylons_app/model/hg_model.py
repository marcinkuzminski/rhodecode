#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 marcink.  All rights reserved.
#
'''
Created on Apr 9, 2010

@author: marcink
'''

from beaker.cache import cache_region
from mercurial import ui
from mercurial.hgweb.hgwebdir_mod import findrepos
from pylons import app_globals as g
from vcs.exceptions import RepositoryError, VCSError
import logging
import os
import sys
log = logging.getLogger(__name__)

try:
    from vcs.backends.hg import MercurialRepository
except ImportError:
    sys.stderr.write('You have to import vcs module')
    raise Exception('Unable to import vcs')


@cache_region('long_term', 'cached_repo_list')
def _get_repos_cached():
    """
    return cached dict with repos
    """
    return HgModel.repo_scan(g.paths[0][0], g.paths[0][1], g.baseui)

@cache_region('long_term', 'full_changelog')
def _full_changelog_cached(repo_name):
    log.info('getting full changelog for %s', repo_name)
    return list(reversed(list(HgModel().get_repo(repo_name))))

class HgModel(object):
    """
    Mercurial Model
    """

    def __init__(self):
        """
        Constructor
        """
        pass
    
    @staticmethod
    def repo_scan(repos_prefix, repos_path, baseui):
        """
        Listing of repositories in given path. This path should not be a 
        repository itself. Return a dictionary of repository objects
        :param repos_path: path to directory it could take syntax with 
        * or ** for deep recursive displaying repositories
        """
        def check_repo_dir(path):
            """
            Checks the repository
            :param path:
            """
            repos_path = path.split('/')
            if repos_path[-1] in ['*', '**']:
                repos_path = repos_path[:-1]
            if repos_path[0] != '/':
                repos_path[0] = '/'
            if not os.path.isdir(os.path.join(*repos_path)):
                raise RepositoryError('Not a valid repository in %s' % path[0][1])        
        if not repos_path.endswith('*'):
            raise VCSError('You need to specify * or ** at the end of path '
                            'for recursive scanning')
            
        check_repo_dir(repos_path)
        log.info('scanning for repositories in %s', repos_path)
        repos = findrepos([(repos_prefix, repos_path)])
        if not isinstance(baseui, ui.ui):
            baseui = ui.ui()
    
        repos_list = {}
        for name, path in repos:
            try:
                #name = name.split('/')[-1]
                if repos_list.has_key(name):
                    raise RepositoryError('Duplicate repository name %s found in'
                                    ' %s' % (name, path))
                else:
                    repos_list[name] = MercurialRepository(path, baseui=baseui)
                    repos_list[name].name = name
            except OSError:
                continue
        return repos_list
        
    def get_repos(self):
        for name, repo in _get_repos_cached().items():
            if repo._get_hidden():
                #skip hidden web repository
                continue
            
            last_change = repo.last_change
            try:
                tip = repo.get_changeset('tip')
            except RepositoryError:
                from pylons_app.lib.utils import EmptyChangeset
                tip = EmptyChangeset()
                
            tmp_d = {}
            tmp_d['name'] = repo.name
            tmp_d['name_sort'] = tmp_d['name'].lower()
            tmp_d['description'] = repo.description
            tmp_d['description_sort'] = tmp_d['description']
            tmp_d['last_change'] = last_change
            tmp_d['last_change_sort'] = last_change[1] - last_change[0]
            tmp_d['tip'] = tip.raw_id
            tmp_d['tip_sort'] = tip.revision 
            tmp_d['rev'] = tip.revision
            tmp_d['contact'] = repo.contact
            tmp_d['contact_sort'] = tmp_d['contact']
            tmp_d['repo_archives'] = list(repo._get_archives())
            
            yield tmp_d

    def get_repo(self, repo_name):
        return _get_repos_cached()[repo_name]
