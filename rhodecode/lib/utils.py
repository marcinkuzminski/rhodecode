# -*- coding: utf-8 -*-
"""
    rhodecode.lib.utils
    ~~~~~~~~~~~~~~~~~~~

    Utilities library for RhodeCode

    :created_on: Apr 18, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import logging
import datetime
import traceback
import paste
import beaker
import tarfile
import shutil
from os.path import abspath
from os.path import dirname as dn, join as jn

from paste.script.command import Command, BadCommand

from mercurial import ui, config

from webhelpers.text import collapse, remove_formatting, strip_tags

from rhodecode.lib.vcs import get_backend
from rhodecode.lib.vcs.backends.base import BaseChangeset
from rhodecode.lib.vcs.utils.lazy import LazyProperty
from rhodecode.lib.vcs.utils.helpers import get_scm
from rhodecode.lib.vcs.exceptions import VCSError

from rhodecode.lib.caching_query import FromCache

from rhodecode.model import meta
from rhodecode.model.db import Repository, User, RhodeCodeUi, \
    UserLog, RepoGroup, RhodeCodeSetting, UserRepoGroupToPerm
from rhodecode.model.meta import Session
from rhodecode.model.repos_group import ReposGroupModel

log = logging.getLogger(__name__)


def recursive_replace(str_, replace=' '):
    """Recursive replace of given sign to just one instance

    :param str_: given string
    :param replace: char to find and replace multiple instances

    Examples::
    >>> recursive_replace("Mighty---Mighty-Bo--sstones",'-')
    'Mighty-Mighty-Bo-sstones'
    """

    if str_.find(replace * 2) == -1:
        return str_
    else:
        str_ = str_.replace(replace * 2, replace)
        return recursive_replace(str_, replace)


def repo_name_slug(value):
    """Return slug of name of repository
    This function is called on each creation/modification
    of repository to prevent bad names in repo
    """

    slug = remove_formatting(value)
    slug = strip_tags(slug)

    for c in """=[]\;'"<>,/~!@#$%^&*()+{}|: """:
        slug = slug.replace(c, '-')
    slug = recursive_replace(slug, '-')
    slug = collapse(slug, '-')
    return slug


def get_repo_slug(request):
    return request.environ['pylons.routes_dict'].get('repo_name')


def get_repos_group_slug(request):
    return request.environ['pylons.routes_dict'].get('group_name')


def action_logger(user, action, repo, ipaddr='', sa=None, commit=False):
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
        sa = meta.Session

    try:
        if hasattr(user, 'user_id'):
            user_obj = user
        elif isinstance(user, basestring):
            user_obj = User.get_by_username(user)
        else:
            raise Exception('You have to provide user object or username')

        if hasattr(repo, 'repo_id'):
            repo_obj = Repository.get(repo.repo_id)
            repo_name = repo_obj.repo_name
        elif  isinstance(repo, basestring):
            repo_name = repo.lstrip('/')
            repo_obj = Repository.get_by_repo_name(repo_name)
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

        log.info('Adding user %s, action %s on %s' % (user_obj, action, repo))
        if commit:
            sa.commit()
    except:
        log.error(traceback.format_exc())
        raise


def get_repos(path, recursive=False):
    """
    Scans given path for repos and return (name,(type,path)) tuple

    :param path: path to scan for repositories
    :param recursive: recursive search and return names with subdirs in front
    """

    # remove ending slash for better results
    path = path.rstrip(os.sep)

    def _get_repos(p):
        if not os.access(p, os.W_OK):
            return
        for dirpath in os.listdir(p):
            if os.path.isfile(os.path.join(p, dirpath)):
                continue
            cur_path = os.path.join(p, dirpath)
            try:
                scm_info = get_scm(cur_path)
                yield scm_info[1].split(path, 1)[-1].lstrip(os.sep), scm_info
            except VCSError:
                if not recursive:
                    continue
                #check if this dir containts other repos for recursive scan
                rec_path = os.path.join(p, dirpath)
                if os.path.isdir(rec_path):
                    for inner_scm in _get_repos(rec_path):
                        yield inner_scm

    return _get_repos(path)


def is_valid_repo(repo_name, base_path):
    """
    Returns True if given path is a valid repository False otherwise
    :param repo_name:
    :param base_path:

    :return True: if given path is a valid repository
    """
    full_path = os.path.join(base_path, repo_name)

    try:
        get_scm(full_path)
        return True
    except VCSError:
        return False


def is_valid_repos_group(repos_group_name, base_path):
    """
    Returns True if given path is a repos group False otherwise

    :param repo_name:
    :param base_path:
    """
    full_path = os.path.join(base_path, repos_group_name)

    # check if it's not a repo
    if is_valid_repo(repos_group_name, base_path):
        return False

    # check if it's a valid path
    if os.path.isdir(full_path):
        return True

    return False


def ask_ok(prompt, retries=4, complaint='Yes or no, please!'):
    while True:
        ok = raw_input(prompt)
        if ok in ('y', 'ye', 'yes'):
            return True
        if ok in ('n', 'no', 'nop', 'nope'):
            return False
        retries = retries - 1
        if retries < 0:
            raise IOError
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
    """A function that will read python rc files or database
    and make an mercurial ui object from read options

    :param path: path to mercurial config file
    :param checkpaths: check the path
    :param read_from: read from 'file' or 'db'
    """

    baseui = ui.ui()

    # clean the baseui object
    baseui._ocfg = config.config()
    baseui._ucfg = config.config()
    baseui._tcfg = config.config()

    if read_from == 'file':
        if not os.path.isfile(path):
            log.debug('hgrc file is not present at %s skipping...' % path)
            return False
        log.debug('reading hgrc from %s' % path)
        cfg = config.config()
        cfg.read(path)
        for section in ui_sections:
            for k, v in cfg.items(section):
                log.debug('settings ui from file[%s]%s:%s' % (section, k, v))
                baseui.setconfig(section, k, v)

    elif read_from == 'db':
        sa = meta.Session
        ret = sa.query(RhodeCodeUi)\
            .options(FromCache("sql_cache_short", "get_hg_ui_settings"))\
            .all()

        hg_ui = ret
        for ui_ in hg_ui:
            if ui_.ui_active:
                log.debug('settings ui from db[%s]%s:%s', ui_.ui_section,
                          ui_.ui_key, ui_.ui_value)
                baseui.setconfig(ui_.ui_section, ui_.ui_key, ui_.ui_value)

        meta.Session.remove()
    return baseui


def set_rhodecode_config(config):
    """
    Updates pylons config with new settings from database

    :param config:
    """
    hgsettings = RhodeCodeSetting.get_app_settings()

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

    def __init__(self, cs='0' * 40, repo=None, requested_revision=None,
                 alias=None):
        self._empty_cs = cs
        self.revision = -1
        self.message = ''
        self.author = ''
        self.date = ''
        self.repository = repo
        self.requested_revision = requested_revision
        self.alias = alias

    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifying this changeset, useful for web
        representation.
        """

        return self._empty_cs

    @LazyProperty
    def branch(self):
        return get_backend(self.alias).DEFAULT_BRANCH_NAME

    @LazyProperty
    def short_id(self):
        return self.raw_id[:12]

    def get_file_changeset(self, path):
        return self

    def get_file_content(self, path):
        return u''

    def get_file_size(self, path):
        return 0


def map_groups(groups):
    """
    Checks for groups existence, and creates groups structures.
    It returns last group in structure

    :param groups: list of groups structure
    """
    sa = meta.Session

    parent = None
    group = None

    # last element is repo in nested groups structure
    groups = groups[:-1]
    rgm = ReposGroupModel(sa)
    for lvl, group_name in enumerate(groups):
        group_name = '/'.join(groups[:lvl] + [group_name])
        group = RepoGroup.get_by_group_name(group_name)
        desc = '%s group' % group_name

#        # WTF that doesn't work !?
#        if group is None:
#            group = rgm.create(group_name, desc, parent, just_db=True)
#            sa.commit()

        if group is None:
            log.debug('creating group level: %s group_name: %s' % (lvl, group_name))
            group = RepoGroup(group_name, parent)
            group.group_description = desc
            sa.add(group)
            rgm._create_default_perms(group)
            sa.commit()
        parent = group
    return group


def repo2db_mapper(initial_repo_list, remove_obsolete=False):
    """
    maps all repos given in initial_repo_list, non existing repositories
    are created, if remove_obsolete is True it also check for db entries
    that are not in initial_repo_list and removes them.

    :param initial_repo_list: list of repositories found by scanning methods
    :param remove_obsolete: check for obsolete entries in database
    """
    from rhodecode.model.repo import RepoModel
    sa = meta.Session
    rm = RepoModel()
    user = sa.query(User).filter(User.admin == True).first()
    if user is None:
        raise Exception('Missing administrative account !')
    added = []

    for name, repo in initial_repo_list.items():
        group = map_groups(name.split(Repository.url_sep()))
        if not rm.get_by_repo_name(name, cache=False):
            log.info('repository %s not found creating default' % name)
            added.append(name)
            form_data = {
             'repo_name': name,
             'repo_name_full': name,
             'repo_type': repo.alias,
             'description': repo.description \
                if repo.description != 'unknown' else '%s repository' % name,
             'private': False,
             'group_id': getattr(group, 'group_id', None)
            }
            rm.create(form_data, user, just_db=True)
    sa.commit()
    removed = []
    if remove_obsolete:
        #remove from database those repositories that are not in the filesystem
        for repo in sa.query(Repository).all():
            if repo.repo_name not in initial_repo_list.keys():
                removed.append(repo.repo_name)
                sa.delete(repo)
                sa.commit()

    return added, removed


# set cache regions for beaker so celery can utilise it
def add_cache(settings):
    cache_settings = {'regions': None}
    for key in settings.keys():
        for prefix in ['beaker.cache.', 'cache.']:
            if key.startswith(prefix):
                name = key.split(prefix)[1].strip()
                cache_settings[name] = settings[key].strip()
    if cache_settings['regions']:
        for region in cache_settings['regions'].split(','):
            region = region.strip()
            region_settings = {}
            for key, value in cache_settings.items():
                if key.startswith(region):
                    region_settings[key.split('.')[1]] = value
            region_settings['expire'] = int(region_settings.get('expire',
                                                                60))
            region_settings.setdefault('lock_dir',
                                       cache_settings.get('lock_dir'))
            region_settings.setdefault('data_dir',
                                       cache_settings.get('data_dir'))

            if 'type' not in region_settings:
                region_settings['type'] = cache_settings.get('type',
                                                             'memory')
            beaker.cache.cache_regions[region] = region_settings


#==============================================================================
# TEST FUNCTIONS AND CREATORS
#==============================================================================
def create_test_index(repo_location, config, full_index):
    """
    Makes default test index

    :param config: test config
    :param full_index:
    """

    from rhodecode.lib.indexers.daemon import WhooshIndexingDaemon
    from rhodecode.lib.pidlock import DaemonLock, LockHeld

    repo_location = repo_location

    index_location = os.path.join(config['app_conf']['index_dir'])
    if not os.path.exists(index_location):
        os.makedirs(index_location)

    try:
        l = DaemonLock(file_=jn(dn(index_location), 'make_index.lock'))
        WhooshIndexingDaemon(index_location=index_location,
                             repo_location=repo_location)\
            .run(full_index=full_index)
        l.release()
    except LockHeld:
        pass


def create_test_env(repos_test_path, config):
    """
    Makes a fresh database and
    install test repository into tmp dir
    """
    from rhodecode.lib.db_manage import DbManage
    from rhodecode.tests import HG_REPO, TESTS_TMP_PATH

    # PART ONE create db
    dbconf = config['sqlalchemy.db1.url']
    log.debug('making test db %s' % dbconf)

    # create test dir if it doesn't exist
    if not os.path.isdir(repos_test_path):
        log.debug('Creating testdir %s' % repos_test_path)
        os.makedirs(repos_test_path)

    dbmanage = DbManage(log_sql=True, dbconf=dbconf, root=config['here'],
                        tests=True)
    dbmanage.create_tables(override=True)
    dbmanage.create_settings(dbmanage.config_prompt(repos_test_path))
    dbmanage.create_default_user()
    dbmanage.admin_prompt()
    dbmanage.create_permissions()
    dbmanage.populate_default_permissions()
    Session.commit()
    # PART TWO make test repo
    log.debug('making test vcs repositories')

    idx_path = config['app_conf']['index_dir']
    data_path = config['app_conf']['cache_dir']

    #clean index and data
    if idx_path and os.path.exists(idx_path):
        log.debug('remove %s' % idx_path)
        shutil.rmtree(idx_path)

    if data_path and os.path.exists(data_path):
        log.debug('remove %s' % data_path)
        shutil.rmtree(data_path)

    #CREATE DEFAULT HG REPOSITORY
    cur_dir = dn(dn(abspath(__file__)))
    tar = tarfile.open(jn(cur_dir, 'tests', "vcs_test_hg.tar.gz"))
    tar.extractall(jn(TESTS_TMP_PATH, HG_REPO))
    tar.close()


#==============================================================================
# PASTER COMMANDS
#==============================================================================
class BasePasterCommand(Command):
    """
    Abstract Base Class for paster commands.

    The celery commands are somewhat aggressive about loading
    celery.conf, and since our module sets the `CELERY_LOADER`
    environment variable to our loader, we have to bootstrap a bit and
    make sure we've had a chance to load the pylons config off of the
    command line, otherwise everything fails.
    """
    min_args = 1
    min_args_error = "Please provide a paster config file as an argument."
    takes_config_file = 1
    requires_config_file = True

    def notify_msg(self, msg, log=False):
        """Make a notification to user, additionally if logger is passed
        it logs this action using given logger

        :param msg: message that will be printed to user
        :param log: logging instance, to use to additionally log this message

        """
        if log and isinstance(log, logging):
            log(msg)

    def run(self, args):
        """
        Overrides Command.run

        Checks for a config file argument and loads it.
        """
        if len(args) < self.min_args:
            raise BadCommand(
                self.min_args_error % {'min_args': self.min_args,
                                       'actual_args': len(args)})

        # Decrement because we're going to lob off the first argument.
        # @@ This is hacky
        self.min_args -= 1
        self.bootstrap_config(args[0])
        self.update_parser()
        return super(BasePasterCommand, self).run(args[1:])

    def update_parser(self):
        """
        Abstract method.  Allows for the class's parser to be updated
        before the superclass's `run` method is called.  Necessary to
        allow options/arguments to be passed through to the underlying
        celery command.
        """
        raise NotImplementedError("Abstract Method.")

    def bootstrap_config(self, conf):
        """
        Loads the pylons configuration.
        """
        from pylons import config as pylonsconfig

        path_to_ini_file = os.path.realpath(conf)
        conf = paste.deploy.appconfig('config:' + path_to_ini_file)
        pylonsconfig.init_app(conf.global_conf, conf.local_conf)
