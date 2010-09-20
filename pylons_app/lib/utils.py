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

"""
Created on April 18, 2010
Utilities for hg app
@author: marcink
"""
from beaker.cache import cache_region
from mercurial import ui, config, hg
from mercurial.error import RepoError
from pylons_app.model import meta
from pylons_app.model.db import Repository, User, HgAppUi, HgAppSettings
from vcs.backends.base import BaseChangeset
from vcs.utils.lazy import LazyProperty
import logging
import os

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

def ask_ok(prompt, retries=4, complaint='Yes or no, please!'):
    while True:
        ok = raw_input(prompt)
        if ok in ('y', 'ye', 'yes'): return True
        if ok in ('n', 'no', 'nop', 'nope'): return False
        retries = retries - 1
        if retries < 0: raise IOError
        print complaint
        
@cache_region('super_short_term', 'cached_hg_ui')
def get_hg_ui_cached():
    try:
        sa = meta.Session
        ret = sa.query(HgAppUi).all()
    finally:
        meta.Session.remove()
    return ret


def get_hg_settings():
    try:
        sa = meta.Session
        ret = sa.query(HgAppSettings).all()
    finally:
        meta.Session.remove()
        
    if not ret:
        raise Exception('Could not get application settings !')
    settings = {}
    for each in ret:
        settings['hg_app_' + each.app_settings_name] = each.app_settings_value    
    
    return settings

def get_hg_ui_settings():
    try:
        sa = meta.Session
        ret = sa.query(HgAppUi).all()
    finally:
        meta.Session.remove()
        
    if not ret:
        raise Exception('Could not get application ui settings !')
    settings = {}
    for each in ret:
        k = each.ui_key
        v = each.ui_value
        if k == '/':
            k = 'root_path'
        
        if k.find('.') != -1:
            k = k.replace('.', '_')
        
        if each.ui_section == 'hooks':
            v = each.ui_active
        
        settings[each.ui_section + '_' + k] = v  
    
    return settings

#propagated from mercurial documentation
ui_sections = ['alias', 'auth',
                'decode/encode', 'defaults',
                'diff', 'email',
                'extensions', 'format',
                'merge-patterns', 'merge-tools',
                'hooks', 'http_proxy',
                'smtp', 'patch',
                'paths', 'profiling',
                'server', 'trusted',
                'ui', 'web', ]
        
def make_ui(read_from='file', path=None, checkpaths=True):        
    """
    A function that will read python rc files or database
    and make an mercurial ui object from read options
    
    @param path: path to mercurial config file
    @param checkpaths: check the path
    @param read_from: read from 'file' or 'db'
    """

    baseui = ui.ui()

    if read_from == 'file':
        if not os.path.isfile(path):
            log.warning('Unable to read config file %s' % path)
            return False
        log.debug('reading hgrc from %s', path)
        cfg = config.config()
        cfg.read(path)
        for section in ui_sections:
            for k, v in cfg.items(section):
                baseui.setconfig(section, k, v)
                log.debug('settings ui from file[%s]%s:%s', section, k, v)
        if checkpaths:check_repo_dir(cfg.items('paths'))                
              
        
    elif read_from == 'db':
        hg_ui = get_hg_ui_cached()
        for ui_ in hg_ui:
            if ui_.ui_active:
                log.debug('settings ui from db[%s]%s:%s', ui_.ui_section, ui_.ui_key, ui_.ui_value)
                baseui.setconfig(ui_.ui_section, ui_.ui_key, ui_.ui_value)
        
    
    return baseui


def set_hg_app_config(config):
    hgsettings = get_hg_settings()
    
    for k, v in hgsettings.items():
        config[k] = v

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
        
class EmptyChangeset(BaseChangeset):
    
    revision = -1
    message = ''
    author = ''
    
    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifing this changeset, useful for web
        representation.
        """
        return '0' * 12


def repo2db_mapper(initial_repo_list, remove_obsolete=False):
    """
    maps all found repositories into db
    """
    from pylons_app.model.repo_model import RepoModel
    
    sa = meta.Session
    user = sa.query(User).filter(User.admin == True).first()
    
    rm = RepoModel()
    
    for name, repo in initial_repo_list.items():
        if not sa.query(Repository).filter(Repository.repo_name == name).scalar():
            log.info('repository %s not found creating default', name)
                
            form_data = {
                         'repo_name':name,
                         'description':repo.description if repo.description != 'unknown' else \
                                        'auto description for %s' % name,
                         'private':False
                         }
            rm.create(form_data, user, just_db=True)


    if remove_obsolete:
        #remove from database those repositories that are not in the filesystem
        for repo in sa.query(Repository).all():
            if repo.repo_name not in initial_repo_list.keys():
                sa.delete(repo)
                sa.commit()

    
    meta.Session.remove()

from UserDict import DictMixin

class OrderedDict(dict, DictMixin):

    def __init__(self, *args, **kwds):
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__end
        except AttributeError:
            self.clear()
        self.update(*args, **kwds)

    def clear(self):
        self.__end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.__map = {}                 # key --> [key, prev, next]
        dict.clear(self)

    def __setitem__(self, key, value):
        if key not in self:
            end = self.__end
            curr = end[1]
            curr[2] = end[1] = self.__map[key] = [key, curr, end]
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        key, prev, next = self.__map.pop(key)
        prev[2] = next
        next[1] = prev

    def __iter__(self):
        end = self.__end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.__end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def popitem(self, last=True):
        if not self:
            raise KeyError('dictionary is empty')
        if last:
            key = reversed(self).next()
        else:
            key = iter(self).next()
        value = self.pop(key)
        return key, value

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        tmp = self.__map, self.__end
        del self.__map, self.__end
        inst_dict = vars(self).copy()
        self.__map, self.__end = tmp
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def keys(self):
        return list(self)

    setdefault = DictMixin.setdefault
    update = DictMixin.update
    pop = DictMixin.pop
    values = DictMixin.values
    items = DictMixin.items
    iterkeys = DictMixin.iterkeys
    itervalues = DictMixin.itervalues
    iteritems = DictMixin.iteritems

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, self.items())

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        if isinstance(other, OrderedDict):
            return len(self) == len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other


#===============================================================================
# TEST FUNCTIONS
#===============================================================================
def create_test_index(repo_location, full_index):
    """Makes default test index
    @param repo_location:
    @param full_index:
    """
    from pylons_app.lib.indexers import daemon
    from pylons_app.lib.indexers.daemon import WhooshIndexingDaemon
    from pylons_app.lib.indexers.pidlock import DaemonLock, LockHeld
    from pylons_app.lib.indexers import IDX_LOCATION
    import shutil
    
    if os.path.exists(IDX_LOCATION):
        shutil.rmtree(IDX_LOCATION)
         
    try:
        l = DaemonLock()
        WhooshIndexingDaemon(repo_location=repo_location)\
            .run(full_index=full_index)
        l.release()
    except LockHeld:
        pass    
    
def create_test_env(repos_test_path, config):
    """Makes a fresh database and 
    install test repository into tmp dir
    """
    from pylons_app.lib.db_manage import DbManage
    import tarfile
    import shutil
    from os.path import dirname as dn, join as jn, abspath
    
    log = logging.getLogger('TestEnvCreator')
    # create logger
    log.setLevel(logging.DEBUG)
    log.propagate = True
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # add formatter to ch
    ch.setFormatter(formatter)
    
    # add ch to logger
    log.addHandler(ch)
    
    #PART ONE create db
    log.debug('making test db')
    dbname = config['sqlalchemy.db1.url'].split('/')[-1]
    dbmanage = DbManage(log_sql=True, dbname=dbname, tests=True)
    dbmanage.create_tables(override=True)
    dbmanage.config_prompt(repos_test_path)
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()
    
    #PART TWO make test repo
    log.debug('making test vcs repo')
    if os.path.isdir('/tmp/vcs_test'):
        shutil.rmtree('/tmp/vcs_test')
        
    cur_dir = dn(dn(abspath(__file__)))
    tar = tarfile.open(jn(cur_dir, 'tests', "vcs_test.tar.gz"))
    tar.extractall('/tmp')
    tar.close()
