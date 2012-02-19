# -*- coding: utf-8 -*-
"""
    rhodecode.lib.db_manage
    ~~~~~~~~~~~~~~~~~~~~~~~

    Database creation, and setup module for RhodeCode. Used for creation
    of database as well as for migration operations

    :created_on: Apr 10, 2010
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
import sys
import uuid
import logging
from os.path import dirname as dn, join as jn

from rhodecode import __dbversion__
from rhodecode.model import meta

from rhodecode.model.user import UserModel
from rhodecode.lib.utils import ask_ok
from rhodecode.model import init_model
from rhodecode.model.db import User, Permission, RhodeCodeUi, \
    RhodeCodeSetting, UserToPerm, DbMigrateVersion, RepoGroup,\
    UserRepoGroupToPerm

from sqlalchemy.engine import create_engine
from rhodecode.model.repos_group import ReposGroupModel

log = logging.getLogger(__name__)


class DbManage(object):
    def __init__(self, log_sql, dbconf, root, tests=False):
        self.dbname = dbconf.split('/')[-1]
        self.tests = tests
        self.root = root
        self.dburi = dbconf
        self.log_sql = log_sql
        self.db_exists = False
        self.init_db()

    def init_db(self):
        engine = create_engine(self.dburi, echo=self.log_sql)
        init_model(engine)
        self.sa = meta.Session

    def create_tables(self, override=False):
        """
        Create a auth database
        """

        log.info("Any existing database is going to be destroyed")
        if self.tests:
            destroy = True
        else:
            destroy = ask_ok('Are you sure to destroy old database ? [y/n]')
        if not destroy:
            sys.exit()
        if destroy:
            meta.Base.metadata.drop_all()

        checkfirst = not override
        meta.Base.metadata.create_all(checkfirst=checkfirst)
        log.info('Created tables for %s' % self.dbname)

    def set_db_version(self):
        ver = DbMigrateVersion()
        ver.version = __dbversion__
        ver.repository_id = 'rhodecode_db_migrations'
        ver.repository_path = 'versions'
        self.sa.add(ver)
        log.info('db version set to: %s' % __dbversion__)

    def upgrade(self):
        """
        Upgrades given database schema to given revision following
        all needed steps, to perform the upgrade

        """

        from rhodecode.lib.dbmigrate.migrate.versioning import api
        from rhodecode.lib.dbmigrate.migrate.exceptions import \
            DatabaseNotControlledError

        if 'sqlite' in self.dburi:
            print (
               '********************** WARNING **********************\n'
               'Make sure your version of sqlite is at least 3.7.X.  \n'
               'Earlier versions are known to fail on some migrations\n'
               '*****************************************************\n'
            )
        upgrade = ask_ok('You are about to perform database upgrade, make '
                         'sure You backed up your database before. '
                         'Continue ? [y/n]')
        if not upgrade:
            sys.exit('Nothing done')

        repository_path = jn(dn(dn(dn(os.path.realpath(__file__)))),
                             'rhodecode/lib/dbmigrate')
        db_uri = self.dburi

        try:
            curr_version = api.db_version(db_uri, repository_path)
            msg = ('Found current database under version'
                 ' control with version %s' % curr_version)

        except (RuntimeError, DatabaseNotControlledError):
            curr_version = 1
            msg = ('Current database is not under version control. Setting'
                   ' as version %s' % curr_version)
            api.version_control(db_uri, repository_path, curr_version)

        print (msg)

        if curr_version == __dbversion__:
            sys.exit('This database is already at the newest version')

        #======================================================================
        # UPGRADE STEPS
        #======================================================================
        class UpgradeSteps(object):
            """
            Those steps follow schema versions so for example schema
            for example schema with seq 002 == step_2 and so on.
            """

            def __init__(self, klass):
                self.klass = klass

            def step_0(self):
                # step 0 is the schema upgrade, and than follow proper upgrades
                print ('attempting to do database upgrade to version %s' \
                                % __dbversion__)
                api.upgrade(db_uri, repository_path, __dbversion__)
                print ('Schema upgrade completed')

            def step_1(self):
                pass

            def step_2(self):
                print ('Patching repo paths for newer version of RhodeCode')
                self.klass.fix_repo_paths()

                print ('Patching default user of RhodeCode')
                self.klass.fix_default_user()

                log.info('Changing ui settings')
                self.klass.create_ui_settings()

            def step_3(self):
                print ('Adding additional settings into RhodeCode db')
                self.klass.fix_settings()
                print ('Adding ldap defaults')
                self.klass.create_ldap_options(skip_existing=True)

            def step_4(self):
                print ('create permissions and fix groups')
                self.klass.create_permissions()
                self.klass.fixup_groups()

            def step_5(self):
                pass

        upgrade_steps = [0] + range(curr_version + 1, __dbversion__ + 1)

        # CALL THE PROPER ORDER OF STEPS TO PERFORM FULL UPGRADE
        for step in upgrade_steps:
            print ('performing upgrade step %s' % step)
            getattr(UpgradeSteps(self), 'step_%s' % step)()
            self.sa.commit()

    def fix_repo_paths(self):
        """
        Fixes a old rhodecode version path into new one without a '*'
        """

        paths = self.sa.query(RhodeCodeUi)\
                .filter(RhodeCodeUi.ui_key == '/')\
                .scalar()

        paths.ui_value = paths.ui_value.replace('*', '')

        try:
            self.sa.add(paths)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise

    def fix_default_user(self):
        """
        Fixes a old default user with some 'nicer' default values,
        used mostly for anonymous access
        """
        def_user = self.sa.query(User)\
                .filter(User.username == 'default')\
                .one()

        def_user.name = 'Anonymous'
        def_user.lastname = 'User'
        def_user.email = 'anonymous@rhodecode.org'

        try:
            self.sa.add(def_user)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise

    def fix_settings(self):
        """
        Fixes rhodecode settings adds ga_code key for google analytics
        """

        hgsettings3 = RhodeCodeSetting('ga_code', '')

        try:
            self.sa.add(hgsettings3)
            self.sa.commit()
        except:
            self.sa.rollback()
            raise

    def admin_prompt(self, second=False):
        if not self.tests:
            import getpass

            def get_password():
                password = getpass.getpass('Specify admin password '
                                           '(min 6 chars):')
                confirm = getpass.getpass('Confirm password:')

                if password != confirm:
                    log.error('passwords mismatch')
                    return False
                if len(password) < 6:
                    log.error('password is to short use at least 6 characters')
                    return False

                return password

            username = raw_input('Specify admin username:')

            password = get_password()
            if not password:
                #second try
                password = get_password()
                if not password:
                    sys.exit()

            email = raw_input('Specify admin email:')
            self.create_user(username, password, email, True)
        else:
            log.info('creating admin and regular test users')
            from rhodecode.tests import TEST_USER_ADMIN_LOGIN,\
            TEST_USER_ADMIN_PASS, TEST_USER_ADMIN_EMAIL,\
            TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS,\
            TEST_USER_REGULAR_EMAIL, TEST_USER_REGULAR2_LOGIN, \
            TEST_USER_REGULAR2_PASS, TEST_USER_REGULAR2_EMAIL

            self.create_user(TEST_USER_ADMIN_LOGIN, TEST_USER_ADMIN_PASS,
                             TEST_USER_ADMIN_EMAIL, True)

            self.create_user(TEST_USER_REGULAR_LOGIN, TEST_USER_REGULAR_PASS,
                             TEST_USER_REGULAR_EMAIL, False)

            self.create_user(TEST_USER_REGULAR2_LOGIN, TEST_USER_REGULAR2_PASS,
                             TEST_USER_REGULAR2_EMAIL, False)

    def create_ui_settings(self):
        """
        Creates ui settings, fills out hooks
        and disables dotencode
        """

        #HOOKS
        hooks1_key = RhodeCodeUi.HOOK_UPDATE
        hooks1_ = self.sa.query(RhodeCodeUi)\
            .filter(RhodeCodeUi.ui_key == hooks1_key).scalar()

        hooks1 = RhodeCodeUi() if hooks1_ is None else hooks1_
        hooks1.ui_section = 'hooks'
        hooks1.ui_key = hooks1_key
        hooks1.ui_value = 'hg update >&2'
        hooks1.ui_active = False

        hooks2_key = RhodeCodeUi.HOOK_REPO_SIZE
        hooks2_ = self.sa.query(RhodeCodeUi)\
            .filter(RhodeCodeUi.ui_key == hooks2_key).scalar()

        hooks2 = RhodeCodeUi() if hooks2_ is None else hooks2_
        hooks2.ui_section = 'hooks'
        hooks2.ui_key = hooks2_key
        hooks2.ui_value = 'python:rhodecode.lib.hooks.repo_size'

        hooks3 = RhodeCodeUi()
        hooks3.ui_section = 'hooks'
        hooks3.ui_key = RhodeCodeUi.HOOK_PUSH
        hooks3.ui_value = 'python:rhodecode.lib.hooks.log_push_action'

        hooks4 = RhodeCodeUi()
        hooks4.ui_section = 'hooks'
        hooks4.ui_key = RhodeCodeUi.HOOK_PULL
        hooks4.ui_value = 'python:rhodecode.lib.hooks.log_pull_action'

        # For mercurial 1.7 set backward comapatibility with format
        dotencode_disable = RhodeCodeUi()
        dotencode_disable.ui_section = 'format'
        dotencode_disable.ui_key = 'dotencode'
        dotencode_disable.ui_value = 'false'

        # enable largefiles
        largefiles = RhodeCodeUi()
        largefiles.ui_section = 'extensions'
        largefiles.ui_key = 'largefiles'
        largefiles.ui_value = ''

        self.sa.add(hooks1)
        self.sa.add(hooks2)
        self.sa.add(hooks3)
        self.sa.add(hooks4)
        self.sa.add(largefiles)

    def create_ldap_options(self, skip_existing=False):
        """Creates ldap settings"""

        for k, v in [('ldap_active', 'false'), ('ldap_host', ''),
                    ('ldap_port', '389'), ('ldap_tls_kind', 'PLAIN'),
                    ('ldap_tls_reqcert', ''), ('ldap_dn_user', ''),
                    ('ldap_dn_pass', ''), ('ldap_base_dn', ''),
                    ('ldap_filter', ''), ('ldap_search_scope', ''),
                    ('ldap_attr_login', ''), ('ldap_attr_firstname', ''),
                    ('ldap_attr_lastname', ''), ('ldap_attr_email', '')]:

            if skip_existing and RhodeCodeSetting.get_by_name(k) != None:
                log.debug('Skipping option %s' % k)
                continue
            setting = RhodeCodeSetting(k, v)
            self.sa.add(setting)

    def fixup_groups(self):
        def_usr = User.get_by_username('default')
        for g in RepoGroup.query().all():
            g.group_name = g.get_new_name(g.name)
            self.sa.add(g)
            # get default perm
            default = UserRepoGroupToPerm.query()\
                .filter(UserRepoGroupToPerm.group == g)\
                .filter(UserRepoGroupToPerm.user == def_usr)\
                .scalar()

            if default is None:
                log.debug('missing default permission for group %s adding' % g)
                ReposGroupModel()._create_default_perms(g)

    def config_prompt(self, test_repo_path='', retries=3):
        if retries == 3:
            log.info('Setting up repositories config')

        if not self.tests and not test_repo_path:
            path = raw_input(
                 'Enter a valid path to store repositories. '
                 'All repositories in that path will be added automatically:'
            )
        else:
            path = test_repo_path
        path_ok = True

        # check proper dir
        if not os.path.isdir(path):
            path_ok = False
            log.error('Given path %s is not a valid directory' % path)

        # check write access
        if not os.access(path, os.W_OK) and path_ok:
            path_ok = False
            log.error('No write permission to given path %s' % path)

        if retries == 0:
            sys.exit('max retries reached')
        if path_ok is False:
            retries -= 1
            return self.config_prompt(test_repo_path, retries)

        return path

    def create_settings(self, path):

        self.create_ui_settings()

        #HG UI OPTIONS
        web1 = RhodeCodeUi()
        web1.ui_section = 'web'
        web1.ui_key = 'push_ssl'
        web1.ui_value = 'false'

        web2 = RhodeCodeUi()
        web2.ui_section = 'web'
        web2.ui_key = 'allow_archive'
        web2.ui_value = 'gz zip bz2'

        web3 = RhodeCodeUi()
        web3.ui_section = 'web'
        web3.ui_key = 'allow_push'
        web3.ui_value = '*'

        web4 = RhodeCodeUi()
        web4.ui_section = 'web'
        web4.ui_key = 'baseurl'
        web4.ui_value = '/'

        paths = RhodeCodeUi()
        paths.ui_section = 'paths'
        paths.ui_key = '/'
        paths.ui_value = path

        hgsettings1 = RhodeCodeSetting('realm', 'RhodeCode authentication')
        hgsettings2 = RhodeCodeSetting('title', 'RhodeCode')
        hgsettings3 = RhodeCodeSetting('ga_code', '')

        self.sa.add(web1)
        self.sa.add(web2)
        self.sa.add(web3)
        self.sa.add(web4)
        self.sa.add(paths)
        self.sa.add(hgsettings1)
        self.sa.add(hgsettings2)
        self.sa.add(hgsettings3)

        self.create_ldap_options()

        log.info('created ui config')

    def create_user(self, username, password, email='', admin=False):
        log.info('creating user %s' % username)
        UserModel().create_or_update(username, password, email,
                                     name='RhodeCode', lastname='Admin',
                                     active=True, admin=admin)

    def create_default_user(self):
        log.info('creating default user')
        # create default user for handling default permissions.
        UserModel().create_or_update(username='default',
                              password=str(uuid.uuid1())[:8],
                              email='anonymous@rhodecode.org',
                              name='Anonymous', lastname='User')

    def create_permissions(self):
        # module.(access|create|change|delete)_[name]
        # module.(none|read|write|admin)
        perms = [
         ('repository.none', 'Repository no access'),
         ('repository.read', 'Repository read access'),
         ('repository.write', 'Repository write access'),
         ('repository.admin', 'Repository admin access'),

         ('group.none', 'Repositories Group no access'),
         ('group.read', 'Repositories Group read access'),
         ('group.write', 'Repositories Group write access'),
         ('group.admin', 'Repositories Group admin access'),

         ('hg.admin', 'Hg Administrator'),
         ('hg.create.repository', 'Repository create'),
         ('hg.create.none', 'Repository creation disabled'),
         ('hg.register.none', 'Register disabled'),
         ('hg.register.manual_activate', 'Register new user with RhodeCode '
                                         'without manual activation'),

         ('hg.register.auto_activate', 'Register new user with RhodeCode '
                                        'without auto activation'),
        ]

        for p in perms:
            if not Permission.get_by_key(p[0]):
                new_perm = Permission()
                new_perm.permission_name = p[0]
                new_perm.permission_longname = p[1]
                self.sa.add(new_perm)

    def populate_default_permissions(self):
        log.info('creating default user permissions')

        default_user = self.sa.query(User)\
        .filter(User.username == 'default').scalar()

        reg_perm = UserToPerm()
        reg_perm.user = default_user
        reg_perm.permission = self.sa.query(Permission)\
        .filter(Permission.permission_name == 'hg.register.manual_activate')\
        .scalar()

        create_repo_perm = UserToPerm()
        create_repo_perm.user = default_user
        create_repo_perm.permission = self.sa.query(Permission)\
        .filter(Permission.permission_name == 'hg.create.repository')\
        .scalar()

        default_repo_perm = UserToPerm()
        default_repo_perm.user = default_user
        default_repo_perm.permission = self.sa.query(Permission)\
        .filter(Permission.permission_name == 'repository.read')\
        .scalar()

        self.sa.add(reg_perm)
        self.sa.add(create_repo_perm)
        self.sa.add(default_repo_perm)
