#!/usr/bin/env python
# encoding: utf-8
# Model for RhodeCode
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
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
Model for RhodeCode
@author: marcink
"""
from beaker.cache import cache_region
from mercurial import ui
from rhodecode.lib import helpers as h
from rhodecode.lib.utils import invalidate_cache
from rhodecode.lib.auth import HasRepoPermissionAny
from rhodecode.model import meta
from rhodecode.model.db import Repository, User
from sqlalchemy.orm import joinedload
from vcs.exceptions import RepositoryError, VCSError
import logging
import sys
log = logging.getLogger(__name__)

try:
    from vcs.backends.hg import MercurialRepository
    from vcs.backends.git import GitRepository
except ImportError:
    sys.stderr.write('You have to import vcs module')
    raise Exception('Unable to import vcs')

def _get_repos_cached_initial(app_globals, initial):
    """return cached dict with repos
    """
    g = app_globals
    return HgModel().repo_scan(g.paths[0][1], g.baseui, initial)

@cache_region('long_term', 'cached_repo_list')
def _get_repos_cached():
    """return cached dict with repos
    """
    log.info('getting all repositories list')
    from pylons import app_globals as g
    return HgModel().repo_scan(g.paths[0][1], g.baseui)

@cache_region('super_short_term', 'cached_repos_switcher_list')
def _get_repos_switcher_cached(cached_repo_list):
    repos_lst = []
    for repo in [x for x in cached_repo_list.values()]:
        if HasRepoPermissionAny('repository.write', 'repository.read',
                    'repository.admin')(repo.name, 'main page check'):
            repos_lst.append((repo.name, repo.dbrepo.private,))

    return sorted(repos_lst, key=lambda k:k[0].lower())

@cache_region('long_term', 'full_changelog')
def _full_changelog_cached(repo_name):
    log.info('getting full changelog for %s', repo_name)
    return list(reversed(list(HgModel().get_repo(repo_name))))

class HgModel(object):
    """
    Mercurial Model
    """

    def __init__(self, sa=None):
        if not sa:
            self.sa = meta.Session()
        else:
            self.sa = sa

    def repo_scan(self, repos_path, baseui, initial=False):
        """
        Listing of repositories in given path. This path should not be a 
        repository itself. Return a dictionary of repository objects
        
        :param repos_path: path to directory containing repositories
        :param baseui
        :param initial: initial scann
        """
        log.info('scanning for repositories in %s', repos_path)

        if not isinstance(baseui, ui.ui):
            baseui = ui.ui()

        from rhodecode.lib.utils import get_repos
        repos = get_repos(repos_path)


        repos_list = {}
        for name, path in repos:
            try:
                #name = name.split('/')[-1]
                if repos_list.has_key(name):
                    raise RepositoryError('Duplicate repository name %s found in'
                                    ' %s' % (name, path))
                else:
                    if path[0] == 'hg':
                        repos_list[name] = MercurialRepository(path[1], baseui=baseui)
                        repos_list[name].name = name

                    if path[0] == 'git':
                        repos_list[name] = GitRepository(path[1])
                        repos_list[name].name = name

                    dbrepo = None
                    if not initial:
                        #for initial scann on application first run we don't
                        #have db repos yet.
                        dbrepo = self.sa.query(Repository)\
                            .options(joinedload(Repository.fork))\
                            .filter(Repository.repo_name == name)\
                            .scalar()

                    if dbrepo:
                        log.info('Adding db instance to cached list')
                        repos_list[name].dbrepo = dbrepo
                        repos_list[name].description = dbrepo.description
                        if dbrepo.user:
                            repos_list[name].contact = dbrepo.user.full_contact
                        else:
                            repos_list[name].contact = self.sa.query(User)\
                            .filter(User.admin == True).first().full_contact
            except OSError:
                continue

        return repos_list

    def get_repos(self):
        for name, repo in _get_repos_cached().items():

            if isinstance(repo, MercurialRepository) and repo._get_hidden():
                #skip hidden web repository
                continue

            last_change = repo.last_change
            tip = h.get_changeset_safe(repo, 'tip')

            tmp_d = {}
            tmp_d['name'] = repo.name
            tmp_d['name_sort'] = tmp_d['name'].lower()
            tmp_d['description'] = repo.description
            tmp_d['description_sort'] = tmp_d['description']
            tmp_d['last_change'] = last_change
            tmp_d['last_change_sort'] = last_change[1] - last_change[0]
            tmp_d['tip'] = tip.short_id
            tmp_d['tip_sort'] = tip.revision
            tmp_d['rev'] = tip.revision
            tmp_d['contact'] = repo.contact
            tmp_d['contact_sort'] = tmp_d['contact']
            tmp_d['repo_archives'] = list(repo._get_archives())
            tmp_d['last_msg'] = tip.message
            tmp_d['repo'] = repo
            yield tmp_d

    def get_repo(self, repo_name):
        try:
            repo = _get_repos_cached()[repo_name]
            return repo
        except KeyError:
            #i we're here and we got key errors let's try to invalidate the
            #cahce and try again
            invalidate_cache('cached_repo_list')
            repo = _get_repos_cached()[repo_name]
            return repo



