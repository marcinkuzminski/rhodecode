#!/usr/bin/env python
# encoding: utf-8
# Utilities for RhodeCode
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
Utilities for RhodeCode
@author: marcink
"""

from UserDict import DictMixin
from mercurial import ui, config, hg
from mercurial.error import RepoError
from rhodecode.model import meta
from rhodecode.model.caching_query import FromCache
from rhodecode.model.db import Repository, User, RhodeCodeUi, UserLog
from rhodecode.model.repo import RepoModel
from rhodecode.model.user import UserModel

from vcs.backends.base import BaseChangeset
from paste.script import command
import ConfigParser
from vcs.utils.lazy import LazyProperty
import traceback
import datetime
import logging
import os

log = logging.getLogger(__name__)


def get_repo_slug(request):
    return request.environ['pylons.routes_dict'].get('repo_name')

def action_logger(user, action, repo, ipaddr='', sa=None):
    """
    Action logger for various actions made by users
    
    :param user: user that made this action, can be a unique username string or
        object containing user_id attribute
    :param action: action to log, should be on of predefined unique actions for
        easy translations
    :param repo: string name of repository or object containing repo_id,
        that action was made on
    :param ipaddr: optional ip address from what the action was made
    :param sa: optional sqlalchemy session
    
    """

    if not sa:
        sa = meta.Session()

    try:
        um = UserModel()
        if hasattr(user, 'user_id'):
            user_obj = user
        elif isinstance(user, basestring):
            user_obj = um.get_by_username(user, cache=False)
        else:
            raise Exception('You have to provide user object or username')


        rm = RepoModel()
        if hasattr(repo, 'repo_id'):
            repo_obj = rm.get(repo.repo_id, cache=False)
            repo_name = repo_obj.repo_name
        elif  isinstance(repo, basestring):
            repo_name = repo.lstrip('/')
            repo_obj = rm.get_by_repo_name(repo_name, cache=False)
        else:
            raise Exception('You have to provide repository to action logger')


        user_log = UserLog()
        user_log.user_id = user_obj.user_id
        user_log.action = action

        user_log.repository_id = repo_obj.repo_id
        user_log.repository_name = repo_name

        user_log.action_date = datetime.datetime.now()
        user_log.user_ip = ipaddr
        sa.add(user_log)
        sa.commit()

        log.info('Adding user %s, action %s on %s', user_obj, action, repo)
    except:
        log.error(traceback.format_exc())
        sa.rollback()

def get_repos(path, recursive=False, initial=False):
    """
    Scans given path for repos and return (name,(type,path)) tuple 
    :param prefix:
    :param path:
    :param recursive:
    :param initial:
    """
    from vcs.utils.helpers import get_scm
    from vcs.exceptions import VCSError

    try:
        scm = get_scm(path)
    except:
        pass
    else:
        raise Exception('The given path %s should not be a repository got %s',
                        path, scm)

    for dirpath in os.listdir(path):
        try:
            yield dirpath, get_scm(os.path.join(path, dirpath))
        except VCSError:
            pass

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
    
    :param path: path to mercurial config file
    :param checkpaths: check the path
    :param read_from: read from 'file' or 'db'
    """

    baseui = ui.ui()

    #clean the baseui object
    baseui._ocfg = config.config()
    baseui._ucfg = config.config()
    baseui._tcfg = config.config()

    if read_from == 'file':
        if not os.path.isfile(path):
            log.warning('Unable to read config file %s' % path)
            return False
        log.debug('reading hgrc from %s', path)
        cfg = config.config()
        cfg.read(path)
        for section in ui_sections:
            for k, v in cfg.items(section):
                log.debug('settings ui from file[%s]%s:%s', section, k, v)
                baseui.setconfig(section, k, v)


    elif read_from == 'db':
        sa = meta.Session()
        ret = sa.query(RhodeCodeUi)\
            .options(FromCache("sql_cache_short",
                               "get_hg_ui_settings")).all()
        meta.Session.remove()
        hg_ui = ret
        for ui_ in hg_ui:
            if ui_.ui_active:
                log.debug('settings ui from db[%s]%s:%s', ui_.ui_section, ui_.ui_key, ui_.ui_value)
                baseui.setconfig(ui_.ui_section, ui_.ui_key, ui_.ui_value)
    return baseui


def set_rhodecode_config(config):
    """
    Updates pylons config with new settings from database
    :param config:
    """
    from rhodecode.model.settings import SettingsModel
    hgsettings = SettingsModel().get_app_settings()

    for k, v in hgsettings.items():
        config[k] = v

def invalidate_cache(cache_key, *args):
    """
    Puts cache invalidation task into db for 
    further global cache invalidation
    """
    from rhodecode.model.scm import ScmModel

    if cache_key.startswith('get_repo_cached_'):
        name = cache_key.split('get_repo_cached_')[-1]
        ScmModel().mark_for_invalidation(name)

class EmptyChangeset(BaseChangeset):
    """
    An dummy empty changeset. It's possible to pass hash when creating
    an EmptyChangeset
    """

    def __init__(self, cs='0' * 40):
        self._empty_cs = cs
        self.revision = -1
        self.message = ''
        self.author = ''
        self.date = ''

    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifying this changeset, useful for web
        representation.
        """
        return self._empty_cs

    @LazyProperty
    def short_id(self):
        return self.raw_id[:12]

    def get_file_changeset(self, path):
        return self

    def get_file_content(self, path):
        return u''

    def get_file_size(self, path):
        return 0

def repo2db_mapper(initial_repo_list, remove_obsolete=False):
    """
    maps all found repositories into db
    """

    sa = meta.Session()
    rm = RepoModel()
    user = sa.query(User).filter(User.admin == True).first()

    for name, repo in initial_repo_list.items():
        if not rm.get_by_repo_name(name, cache=False):
            log.info('repository %s not found creating default', name)

            form_data = {
                         'repo_name':name,
                         'repo_type':repo.alias,
                         'description':repo.description \
                            if repo.description != 'unknown' else \
                                        '%s repository' % name,
                         'private':False
                         }
            rm.create(form_data, user, just_db=True)

    if remove_obsolete:
        #remove from database those repositories that are not in the filesystem
        for repo in sa.query(Repository).all():
            if repo.repo_name not in initial_repo_list.keys():
                sa.delete(repo)
                sa.commit()

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
# TEST FUNCTIONS AND CREATORS
#===============================================================================
def create_test_index(repo_location, full_index):
    """Makes default test index
    :param repo_location:
    :param full_index:
    """
    from rhodecode.lib.indexers.daemon import WhooshIndexingDaemon
    from rhodecode.lib.pidlock import DaemonLock, LockHeld
    import shutil

    index_location = os.path.join(repo_location, 'index')
    if os.path.exists(index_location):
        shutil.rmtree(index_location)

    try:
        l = DaemonLock()
        WhooshIndexingDaemon(index_location=index_location,
                             repo_location=repo_location)\
            .run(full_index=full_index)
        l.release()
    except LockHeld:
        pass

def create_test_env(repos_test_path, config):
    """Makes a fresh database and 
    install test repository into tmp dir
    """
    from rhodecode.lib.db_manage import DbManage
    from rhodecode.tests import HG_REPO, GIT_REPO, NEW_HG_REPO, NEW_GIT_REPO, \
        HG_FORK, GIT_FORK, TESTS_TMP_PATH
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
    dbname = config['sqlalchemy.db1.url'].split('/')[-1]
    log.debug('making test db %s', dbname)

    dbmanage = DbManage(log_sql=True, dbname=dbname, root=config['here'],
                        tests=True)
    dbmanage.create_tables(override=True)
    dbmanage.config_prompt(repos_test_path)
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()

    #PART TWO make test repo
    log.debug('making test vcs repositories')

    #remove old one from previos tests
    for r in [HG_REPO, GIT_REPO, NEW_HG_REPO, NEW_GIT_REPO, HG_FORK, GIT_FORK]:

        if os.path.isdir(jn(TESTS_TMP_PATH, r)):
            log.debug('removing %s', r)
            shutil.rmtree(jn(TESTS_TMP_PATH, r))

    #CREATE DEFAULT HG REPOSITORY
    cur_dir = dn(dn(abspath(__file__)))
    tar = tarfile.open(jn(cur_dir, 'tests', "vcs_test_hg.tar.gz"))
    tar.extractall(jn(TESTS_TMP_PATH, HG_REPO))
    tar.close()

class UpgradeDb(command.Command):
    """Command used for paster to upgrade our database to newer version
    """

    max_args = 1
    min_args = 1

    usage = "CONFIG_FILE"
    summary = "Upgrades current db to newer version given configuration file"
    group_name = "RhodeCode"

    parser = command.Command.standard_parser(verbose=True)

    parser.add_option('--sql',
                      action='store_true',
                      dest='just_sql',
                      help="Prints upgrade sql for further investigation",
                      default=False)
    def command(self):
        config_name = self.args[0]
        p = config_name.split('/')
        root = '.' if len(p) == 1 else '/'.join(p[:-1])
        config = ConfigParser.ConfigParser({'here':root})
        config.read(config_name)
