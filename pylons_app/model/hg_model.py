#!/usr/bin/env python
# encoding: utf-8
# Model for hg app
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
 
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
Created on April 9, 2010
Model for hg app
@author: marcink
"""

from beaker.cache import cache_region
from mercurial import ui
from mercurial.hgweb.hgwebdir_mod import findrepos
from vcs.exceptions import RepositoryError, VCSError
from pylons_app.model.meta import Session
from pylons_app.model.db import Repository
import logging
import os
import sys
log = logging.getLogger(__name__)

try:
    from vcs.backends.hg import MercurialRepository
except ImportError:
    sys.stderr.write('You have to import vcs module')
    raise Exception('Unable to import vcs')

def _get_repos_cached_initial(app_globals):
    """
    return cached dict with repos
    """
    g = app_globals
    return HgModel.repo_scan(g.paths[0][0], g.paths[0][1], g.baseui)

@cache_region('long_term', 'cached_repo_list')
def _get_repos_cached():
    """
    return cached dict with repos
    """
    log.info('getting all repositories list')
    from pylons import app_globals as g
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
    
    @staticmethod
    def repo_scan(repos_prefix, repos_path, baseui):
        """
        Listing of repositories in given path. This path should not be a 
        repository itself. Return a dictionary of repository objects
        :param repos_path: path to directory it could take syntax with 
        * or ** for deep recursive displaying repositories
        """
        sa = Session()
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
                    dbrepo = sa.query(Repository).get(name)
                    if dbrepo:
                        repos_list[name].description = dbrepo.description
                        repos_list[name].contact = dbrepo.user.full_contact
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
            tmp_d['last_msg'] = tip.message
            
            yield tmp_d

    def get_repo(self, repo_name):
        return _get_repos_cached()[repo_name]
