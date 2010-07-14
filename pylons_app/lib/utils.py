#!/usr/bin/env python
# encoding: utf-8
# Utilities for hg app
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
from beaker.cache import cache_region

"""
Created on April 18, 2010
Utilities for hg app
@author: marcink
"""

import os
import logging
from mercurial import ui, config, hg
from mercurial.error import RepoError
from pylons_app.model.db import Repository, User, HgAppUi
log = logging.getLogger(__name__)


def get_repo_slug(request):
    return request.environ['pylons.routes_dict'].get('repo_name')

def is_mercurial(environ):
    """
    Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
    """
    http_accept = environ.get('HTTP_ACCEPT')
    if http_accept and http_accept.startswith('application/mercurial'):
        return True
    return False

def check_repo_dir(paths):
    repos_path = paths[0][1].split('/')
    if repos_path[-1] in ['*', '**']:
        repos_path = repos_path[:-1]
    if repos_path[0] != '/':
        repos_path[0] = '/'
    if not os.path.isdir(os.path.join(*repos_path)):
        raise Exception('Not a valid repository in %s' % paths[0][1])

def check_repo_fast(repo_name, base_path):
    if os.path.isdir(os.path.join(base_path, repo_name)):return False
    return True

def check_repo(repo_name, base_path, verify=True):

    repo_path = os.path.join(base_path, repo_name)

    try:
        if not check_repo_fast(repo_name, base_path):
            return False
        r = hg.repository(ui.ui(), repo_path)
        if verify:
            hg.verify(r)
        #here we hnow that repo exists it was verified
        log.info('%s repo is already created', repo_name)
        return False
    except RepoError:
        #it means that there is no valid repo there...
        log.info('%s repo is free for creation', repo_name)
        return True


@cache_region('super_short_term', 'cached_hg_ui')
def get_hg_ui_cached():
    from pylons_app.model.meta import Session
    sa = Session()
    return sa.query(HgAppUi).all()    

def make_ui(read_from='file', path=None, checkpaths=True):        
    """
    A function that will read python rc files or database
    and make an mercurial ui object from read options
    
    @param path: path to mercurial config file
    @param checkpaths: check the path
    @param read_from: read from 'file' or 'db'
    """
    #propagated from mercurial documentation
    sections = ['alias', 'auth',
                'decode/encode', 'defaults',
                'diff', 'email',
                'extensions', 'format',
                'merge-patterns', 'merge-tools',
                'hooks', 'http_proxy',
                'smtp', 'patch',
                'paths', 'profiling',
                'server', 'trusted',
                'ui', 'web', ]
    baseui = ui.ui()

                
    if read_from == 'file':
        if not os.path.isfile(path):
            log.warning('Unable to read config file %s' % path)
            return False
        
        cfg = config.config()
        cfg.read(path)
        for section in sections:
            for k, v in cfg.items(section):
                baseui.setconfig(section, k, v)
        if checkpaths:check_repo_dir(cfg.items('paths'))                
              
        
    elif read_from == 'db':
        hg_ui = get_hg_ui_cached()
        for ui_ in hg_ui:
            baseui.setconfig(ui_.ui_section, ui_.ui_key, ui_.ui_value)
        
    
    return baseui


def set_hg_app_config(config):
    config['hg_app_auth_realm'] = 'realm'
    config['hg_app_name'] = 'app name'

def invalidate_cache(name, *args):
    """Invalidates given name cache"""
    
    from beaker.cache import region_invalidate
    log.info('INVALIDATING CACHE FOR %s', name)
    
    """propagate our arguments to make sure invalidation works. First
    argument has to be the name of cached func name give to cache decorator
    without that the invalidation would not work"""
    tmp = [name]
    tmp.extend(args)
    args = tuple(tmp)
    
    if name == 'cached_repo_list':
        from pylons_app.model.hg_model import _get_repos_cached
        region_invalidate(_get_repos_cached, None, *args)
        
    if name == 'full_changelog':
        from pylons_app.model.hg_model import _full_changelog_cached
        region_invalidate(_full_changelog_cached, None, *args)
        
from vcs.backends.base import BaseChangeset
from vcs.utils.lazy import LazyProperty
class EmptyChangeset(BaseChangeset):
    
    revision = -1
    message = ''
    
    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifing this changeset, useful for web
        representation.
        """
        return '0' * 12


def repo2db_mapper(initial_repo_list):
    """
    maps all found repositories into db
    """
    from pylons_app.model.meta import Session
    from pylons_app.model.repo_model import RepoModel
    
    sa = Session()
    user = sa.query(User).filter(User.admin == True).first()
    
    rm = RepoModel()
    
    for name, repo in initial_repo_list.items():
        if not sa.query(Repository).get(name):
            log.info('repository %s not found creating default', name)
                
            form_data = {
                         'repo_name':name,
                         'description':repo.description if repo.description != 'unknown' else \
                                        'auto description for %s' % name,
                         'private':False
                         }
            rm.create(form_data, user, just_db=True)
