# -*- coding: utf-8 -*-
"""
    rhodecode.model.db
    ~~~~~~~~~~~~~~~~~~

    Database Models for RhodeCode

    :created_on: Apr 08, 2010
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
from datetime import date

from sqlalchemy import *
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, joinedload, class_mapper, validates
from beaker.cache import cache_region, region_invalidate

from rhodecode.lib.vcs import get_backend
from rhodecode.lib.vcs.utils.helpers import get_scm
from rhodecode.lib.vcs.exceptions import VCSError
from rhodecode.lib.vcs.utils.lazy import LazyProperty

from rhodecode.lib import str2bool, safe_str, get_changeset_safe, \
    generate_api_key, safe_unicode
from rhodecode.lib.exceptions import UsersGroupsAssignedException
from rhodecode.lib.compat import json

from rhodecode.model.meta import Base, Session
from rhodecode.lib.caching_query import FromCache


log = logging.getLogger(__name__)

#==============================================================================
# BASE CLASSES
#==============================================================================

class ModelSerializer(json.JSONEncoder):
    """
    Simple Serializer for JSON,

    usage::

        to make object customized for serialization implement a __json__
        method that will return a dict for serialization into json

    example::

        class Task(object):

            def __init__(self, name, value):
                self.name = name
                self.value = value

            def __json__(self):
                return dict(name=self.name,
                            value=self.value)

    """

    def default(self, obj):

        if hasattr(obj, '__json__'):
            return obj.__json__()
        else:
            return json.JSONEncoder.default(self, obj)

class BaseModel(object):
    """Base Model for all classess

    """

    @classmethod
    def _get_keys(cls):
        """return column names for this model """
        return class_mapper(cls).c.keys()

    def get_dict(self):
        """return dict with keys and values corresponding
        to this model data """

        d = {}
        for k in self._get_keys():
            d[k] = getattr(self, k)
        return d

    def get_appstruct(self):
        """return list with keys and values tupples corresponding
        to this model data """

        l = []
        for k in self._get_keys():
            l.append((k, getattr(self, k),))
        return l

    def populate_obj(self, populate_dict):
        """populate model with data from given populate_dict"""

        for k in self._get_keys():
            if k in populate_dict:
                setattr(self, k, populate_dict[k])

    @classmethod
    def query(cls):
        return Session.query(cls)

    @classmethod
    def get(cls, id_):
        if id_:
            return cls.query().get(id_)

    @classmethod
    def getAll(cls):
        return cls.query().all()

    @classmethod
    def delete(cls, id_):
        obj = cls.query().get(id_)
        Session.delete(obj)
        Session.commit()


class RhodeCodeSetting(Base, BaseModel):
    __tablename__ = 'rhodecode_settings'
    __table_args__ = (UniqueConstraint('app_settings_name'), {'extend_existing':True})
    app_settings_id = Column("app_settings_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    app_settings_name = Column("app_settings_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    _app_settings_value = Column("app_settings_value", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __init__(self, k='', v=''):
        self.app_settings_name = k
        self.app_settings_value = v


    @validates('_app_settings_value')
    def validate_settings_value(self, key, val):
        assert type(val) == unicode
        return val

    @hybrid_property
    def app_settings_value(self):
        v = self._app_settings_value
        if v == 'ldap_active':
            v = str2bool(v)
        return v

    @app_settings_value.setter
    def app_settings_value(self, val):
        """
        Setter that will always make sure we use unicode in app_settings_value

        :param val:
        """
        self._app_settings_value = safe_unicode(val)

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.app_settings_name, self.app_settings_value)


    @classmethod
    def get_by_name(cls, ldap_key):
        return cls.query()\
            .filter(cls.app_settings_name == ldap_key).scalar()

    @classmethod
    def get_app_settings(cls, cache=False):

        ret = cls.query()

        if cache:
            ret = ret.options(FromCache("sql_cache_short", "get_hg_settings"))

        if not ret:
            raise Exception('Could not get application settings !')
        settings = {}
        for each in ret:
            settings['rhodecode_' + each.app_settings_name] = \
                each.app_settings_value

        return settings

    @classmethod
    def get_ldap_settings(cls, cache=False):
        ret = cls.query()\
                .filter(cls.app_settings_name.startswith('ldap_')).all()
        fd = {}
        for row in ret:
            fd.update({row.app_settings_name:row.app_settings_value})

        return fd


class RhodeCodeUi(Base, BaseModel):
    __tablename__ = 'rhodecode_ui'
    __table_args__ = (UniqueConstraint('ui_key'), {'extend_existing':True})

    HOOK_UPDATE = 'changegroup.update'
    HOOK_REPO_SIZE = 'changegroup.repo_size'
    HOOK_PUSH = 'pretxnchangegroup.push_logger'
    HOOK_PULL = 'preoutgoing.pull_logger'

    ui_id = Column("ui_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    ui_section = Column("ui_section", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_key = Column("ui_key", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_value = Column("ui_value", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_active = Column("ui_active", Boolean(), nullable=True, unique=None, default=True)


    @classmethod
    def get_by_key(cls, key):
        return cls.query().filter(cls.ui_key == key)


    @classmethod
    def get_builtin_hooks(cls):
        q = cls.query()
        q = q.filter(cls.ui_key.in_([cls.HOOK_UPDATE,
                                    cls.HOOK_REPO_SIZE,
                                    cls.HOOK_PUSH, cls.HOOK_PULL]))
        return q.all()

    @classmethod
    def get_custom_hooks(cls):
        q = cls.query()
        q = q.filter(~cls.ui_key.in_([cls.HOOK_UPDATE,
                                    cls.HOOK_REPO_SIZE,
                                    cls.HOOK_PUSH, cls.HOOK_PULL]))
        q = q.filter(cls.ui_section == 'hooks')
        return q.all()

    @classmethod
    def create_or_update_hook(cls, key, val):
        new_ui = cls.get_by_key(key).scalar() or cls()
        new_ui.ui_section = 'hooks'
        new_ui.ui_active = True
        new_ui.ui_key = key
        new_ui.ui_value = val

        Session.add(new_ui)
        Session.commit()


class User(Base, BaseModel):
    __tablename__ = 'users'
    __table_args__ = (UniqueConstraint('username'), UniqueConstraint('email'), {'extend_existing':True})
    user_id = Column("user_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    username = Column("username", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", Boolean(), nullable=True, unique=None, default=None)
    admin = Column("admin", Boolean(), nullable=True, unique=None, default=False)
    name = Column("name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    lastname = Column("lastname", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    email = Column("email", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    last_login = Column("last_login", DateTime(timezone=False), nullable=True, unique=None, default=None)
    ldap_dn = Column("ldap_dn", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    api_key = Column("api_key", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    user_log = relationship('UserLog', cascade='all')
    user_perms = relationship('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all')

    repositories = relationship('Repository')
    user_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')
    repo_to_perm = relationship('UserRepoToPerm', primaryjoin='UserRepoToPerm.user_id==User.user_id', cascade='all')

    group_member = relationship('UsersGroupMember', cascade='all')

    @property
    def full_contact(self):
        return '%s %s <%s>' % (self.name, self.lastname, self.email)

    @property
    def short_contact(self):
        return '%s %s' % (self.name, self.lastname)

    @property
    def is_admin(self):
        return self.admin

    def __repr__(self):
        try:
            return "<%s('id:%s:%s')>" % (self.__class__.__name__,
                                             self.user_id, self.username)
        except:
            return self.__class__.__name__

    @classmethod
    def get_by_username(cls, username, case_insensitive=False):
        if case_insensitive:
            return Session.query(cls).filter(cls.username.ilike(username)).scalar()
        else:
            return Session.query(cls).filter(cls.username == username).scalar()

    @classmethod
    def get_by_api_key(cls, api_key):
        return cls.query().filter(cls.api_key == api_key).one()

    def update_lastlogin(self):
        """Update user lastlogin"""

        self.last_login = datetime.datetime.now()
        Session.add(self)
        Session.commit()
        log.debug('updated user %s lastlogin' % self.username)

    @classmethod
    def create(cls, form_data):
        from rhodecode.lib.auth import get_crypt_password

        try:
            new_user = cls()
            for k, v in form_data.items():
                if k == 'password':
                    v = get_crypt_password(v)
                setattr(new_user, k, v)

            new_user.api_key = generate_api_key(form_data['username'])
            Session.add(new_user)
            Session.commit()
            return new_user
        except:
            log.error(traceback.format_exc())
            Session.rollback()
            raise

class UserLog(Base, BaseModel):
    __tablename__ = 'user_logs'
    __table_args__ = {'extend_existing':True}
    user_log_id = Column("user_log_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)
    repository_name = Column("repository_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    user_ip = Column("user_ip", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", UnicodeText(length=1200000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DateTime(timezone=False), nullable=True, unique=None, default=None)

    @property
    def action_as_day(self):
        return date(*self.action_date.timetuple()[:3])

    user = relationship('User')
    repository = relationship('Repository')


class UsersGroup(Base, BaseModel):
    __tablename__ = 'users_groups'
    __table_args__ = {'extend_existing':True}

    users_group_id = Column("users_group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_name = Column("users_group_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    users_group_active = Column("users_group_active", Boolean(), nullable=True, unique=None, default=None)

    members = relationship('UsersGroupMember', cascade="all, delete, delete-orphan", lazy="joined")

    def __repr__(self):
        return '<userGroup(%s)>' % (self.users_group_name)

    @classmethod
    def get_by_group_name(cls, group_name, cache=False, case_insensitive=False):
        if case_insensitive:
            gr = cls.query()\
                .filter(cls.users_group_name.ilike(group_name))
        else:
            gr = cls.query()\
                .filter(cls.users_group_name == group_name)
        if cache:
            gr = gr.options(FromCache("sql_cache_short",
                                          "get_user_%s" % group_name))
        return gr.scalar()


    @classmethod
    def get(cls, users_group_id, cache=False):
        users_group = cls.query()
        if cache:
            users_group = users_group.options(FromCache("sql_cache_short",
                                    "get_users_group_%s" % users_group_id))
        return users_group.get(users_group_id)

    @classmethod
    def create(cls, form_data):
        try:
            new_users_group = cls()
            for k, v in form_data.items():
                setattr(new_users_group, k, v)

            Session.add(new_users_group)
            Session.commit()
            return new_users_group
        except:
            log.error(traceback.format_exc())
            Session.rollback()
            raise

    @classmethod
    def update(cls, users_group_id, form_data):

        try:
            users_group = cls.get(users_group_id, cache=False)

            for k, v in form_data.items():
                if k == 'users_group_members':
                    users_group.members = []
                    Session.flush()
                    members_list = []
                    if v:
                        v = [v] if isinstance(v, basestring) else v
                        for u_id in set(v):
                            member = UsersGroupMember(users_group_id, u_id)
                            members_list.append(member)
                    setattr(users_group, 'members', members_list)
                setattr(users_group, k, v)

            Session.add(users_group)
            Session.commit()
        except:
            log.error(traceback.format_exc())
            Session.rollback()
            raise

    @classmethod
    def delete(cls, users_group_id):
        try:

            # check if this group is not assigned to repo
            assigned_groups = UsersGroupRepoToPerm.query()\
                .filter(UsersGroupRepoToPerm.users_group_id ==
                        users_group_id).all()

            if assigned_groups:
                raise UsersGroupsAssignedException('RepoGroup assigned to %s' %
                                                   assigned_groups)

            users_group = cls.get(users_group_id, cache=False)
            Session.delete(users_group)
            Session.commit()
        except:
            log.error(traceback.format_exc())
            Session.rollback()
            raise

class UsersGroupMember(Base, BaseModel):
    __tablename__ = 'users_groups_members'
    __table_args__ = {'extend_existing':True}

    users_group_member_id = Column("users_group_member_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)

    user = relationship('User', lazy='joined')
    users_group = relationship('UsersGroup')

    def __init__(self, gr_id='', u_id=''):
        self.users_group_id = gr_id
        self.user_id = u_id

    @staticmethod
    def add_user_to_group(group, user):
        ugm = UsersGroupMember()
        ugm.users_group = group
        ugm.user = user
        Session.add(ugm)
        Session.commit()
        return ugm

class Repository(Base, BaseModel):
    __tablename__ = 'repositories'
    __table_args__ = (UniqueConstraint('repo_name'), {'extend_existing':True},)

    repo_id = Column("repo_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repo_name = Column("repo_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    clone_uri = Column("clone_uri", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=False, default=None)
    repo_type = Column("repo_type", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=False, default='hg')
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", Boolean(), nullable=True, unique=None, default=None)
    enable_statistics = Column("statistics", Boolean(), nullable=True, unique=None, default=True)
    enable_downloads = Column("downloads", Boolean(), nullable=True, unique=None, default=True)
    description = Column("description", String(length=10000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    created_on = Column('created_on', DateTime(timezone=False), nullable=True, unique=None, default=datetime.datetime.now)

    fork_id = Column("fork_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=False, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=False, default=None)


    user = relationship('User')
    fork = relationship('Repository', remote_side=repo_id)
    group = relationship('RepoGroup')
    repo_to_perm = relationship('UserRepoToPerm', cascade='all', order_by='UserRepoToPerm.repo_to_perm_id')
    users_group_to_perm = relationship('UsersGroupRepoToPerm', cascade='all')
    stats = relationship('Statistics', cascade='all', uselist=False)

    followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_repo_id==Repository.repo_id', cascade='all')

    logs = relationship('UserLog', cascade='all')

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.repo_id, self.repo_name)

    @classmethod
    def url_sep(cls):
        return '/'

    @classmethod
    def get_by_repo_name(cls, repo_name):
        q = Session.query(cls).filter(cls.repo_name == repo_name)
        q = q.options(joinedload(Repository.fork))\
                .options(joinedload(Repository.user))\
                .options(joinedload(Repository.group))
        return q.one()

    @classmethod
    def get_repo_forks(cls, repo_id):
        return cls.query().filter(Repository.fork_id == repo_id)

    @classmethod
    def base_path(cls):
        """
        Returns base path when all repos are stored

        :param cls:
        """
        q = Session.query(RhodeCodeUi).filter(RhodeCodeUi.ui_key ==
                                              cls.url_sep())
        q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return q.one().ui_value

    @property
    def just_name(self):
        return self.repo_name.split(Repository.url_sep())[-1]

    @property
    def groups_with_parents(self):
        groups = []
        if self.group is None:
            return groups

        cur_gr = self.group
        groups.insert(0, cur_gr)
        while 1:
            gr = getattr(cur_gr, 'parent_group', None)
            cur_gr = cur_gr.parent_group
            if gr is None:
                break
            groups.insert(0, gr)

        return groups

    @property
    def groups_and_repo(self):
        return self.groups_with_parents, self.just_name

    @LazyProperty
    def repo_path(self):
        """
        Returns base full path for that repository means where it actually
        exists on a filesystem
        """
        q = Session.query(RhodeCodeUi).filter(RhodeCodeUi.ui_key ==
                                              Repository.url_sep())
        q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return q.one().ui_value

    @property
    def repo_full_path(self):
        p = [self.repo_path]
        # we need to split the name by / since this is how we store the
        # names in the database, but that eventually needs to be converted
        # into a valid system path
        p += self.repo_name.split(Repository.url_sep())
        return os.path.join(*p)

    def get_new_name(self, repo_name):
        """
        returns new full repository name based on assigned group and new new

        :param group_name:
        """
        path_prefix = self.group.full_path_splitted if self.group else []
        return Repository.url_sep().join(path_prefix + [repo_name])

    @property
    def _ui(self):
        """
        Creates an db based ui object for this repository
        """
        from mercurial import ui
        from mercurial import config
        baseui = ui.ui()

        #clean the baseui object
        baseui._ocfg = config.config()
        baseui._ucfg = config.config()
        baseui._tcfg = config.config()


        ret = RhodeCodeUi.query()\
            .options(FromCache("sql_cache_short", "repository_repo_ui")).all()

        hg_ui = ret
        for ui_ in hg_ui:
            if ui_.ui_active:
                log.debug('settings ui from db[%s]%s:%s', ui_.ui_section,
                          ui_.ui_key, ui_.ui_value)
                baseui.setconfig(ui_.ui_section, ui_.ui_key, ui_.ui_value)

        return baseui

    @classmethod
    def is_valid(cls, repo_name):
        """
        returns True if given repo name is a valid filesystem repository

        :param cls:
        :param repo_name:
        """
        from rhodecode.lib.utils import is_valid_repo

        return is_valid_repo(repo_name, cls.base_path())


    #==========================================================================
    # SCM PROPERTIES
    #==========================================================================

    def get_changeset(self, rev):
        return get_changeset_safe(self.scm_instance, rev)

    @property
    def tip(self):
        return self.get_changeset('tip')

    @property
    def author(self):
        return self.tip.author

    @property
    def last_change(self):
        return self.scm_instance.last_change

    #==========================================================================
    # SCM CACHE INSTANCE
    #==========================================================================

    @property
    def invalidate(self):
        return CacheInvalidation.invalidate(self.repo_name)

    def set_invalidate(self):
        """
        set a cache for invalidation for this instance
        """
        CacheInvalidation.set_invalidate(self.repo_name)

    @LazyProperty
    def scm_instance(self):
        return self.__get_instance()

    @property
    def scm_instance_cached(self):
        @cache_region('long_term')
        def _c(repo_name):
            return self.__get_instance()
        rn = self.repo_name

        inv = self.invalidate
        if inv is not None:
            region_invalidate(_c, None, rn)
            # update our cache
            CacheInvalidation.set_valid(inv.cache_key)
        return _c(rn)

    def __get_instance(self):

        repo_full_path = self.repo_full_path

        try:
            alias = get_scm(repo_full_path)[0]
            log.debug('Creating instance of %s repository' % alias)
            backend = get_backend(alias)
        except VCSError:
            log.error(traceback.format_exc())
            log.error('Perhaps this repository is in db and not in '
                      'filesystem run rescan repositories with '
                      '"destroy old data " option from admin panel')
            return

        if alias == 'hg':

            repo = backend(safe_str(repo_full_path), create=False,
                           baseui=self._ui)
            # skip hidden web repository
            if repo._get_hidden():
                return
        else:
            repo = backend(repo_full_path, create=False)

        return repo


class RepoGroup(Base, BaseModel):
    __tablename__ = 'groups'
    __table_args__ = (UniqueConstraint('group_name', 'group_parent_id'),
                      CheckConstraint('group_id != group_parent_id'), {'extend_existing':True},)
    __mapper_args__ = {'order_by':'group_name'}

    group_id = Column("group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    group_name = Column("group_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    group_parent_id = Column("group_parent_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=None, default=None)
    group_description = Column("group_description", String(length=10000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    parent_group = relationship('RepoGroup', remote_side=group_id)


    def __init__(self, group_name='', parent_group=None):
        self.group_name = group_name
        self.parent_group = parent_group

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__, self.group_id,
                                  self.group_name)

    @classmethod
    def groups_choices(cls):
        from webhelpers.html import literal as _literal
        repo_groups = [('', '')]
        sep = ' &raquo; '
        _name = lambda k: _literal(sep.join(k))

        repo_groups.extend([(x.group_id, _name(x.full_path_splitted))
                              for x in cls.query().all()])

        repo_groups = sorted(repo_groups, key=lambda t: t[1].split(sep)[0])
        return repo_groups

    @classmethod
    def url_sep(cls):
        return '/'

    @classmethod
    def get_by_group_name(cls, group_name, cache=False, case_insensitive=False):
        if case_insensitive:
            gr = cls.query()\
                .filter(cls.group_name.ilike(group_name))
        else:
            gr = cls.query()\
                .filter(cls.group_name == group_name)
        if cache:
            gr = gr.options(FromCache("sql_cache_short",
                                          "get_group_%s" % group_name))
        return gr.scalar()

    @property
    def parents(self):
        parents_recursion_limit = 5
        groups = []
        if self.parent_group is None:
            return groups
        cur_gr = self.parent_group
        groups.insert(0, cur_gr)
        cnt = 0
        while 1:
            cnt += 1
            gr = getattr(cur_gr, 'parent_group', None)
            cur_gr = cur_gr.parent_group
            if gr is None:
                break
            if cnt == parents_recursion_limit:
                # this will prevent accidental infinit loops
                log.error('group nested more than %s' %
                          parents_recursion_limit)
                break

            groups.insert(0, gr)
        return groups

    @property
    def children(self):
        return Group.query().filter(Group.parent_group == self)

    @property
    def name(self):
        return self.group_name.split(Group.url_sep())[-1]

    @property
    def full_path(self):
        return self.group_name

    @property
    def full_path_splitted(self):
        return self.group_name.split(Group.url_sep())

    @property
    def repositories(self):
        return Repository.query().filter(Repository.group == self)

    @property
    def repositories_recursive_count(self):
        cnt = self.repositories.count()

        def children_count(group):
            cnt = 0
            for child in group.children:
                cnt += child.repositories.count()
                cnt += children_count(child)
            return cnt

        return cnt + children_count(self)


    def get_new_name(self, group_name):
        """
        returns new full group name based on parent and new name

        :param group_name:
        """
        path_prefix = (self.parent_group.full_path_splitted if
                       self.parent_group else [])
        return Group.url_sep().join(path_prefix + [group_name])


class Permission(Base, BaseModel):
    __tablename__ = 'permissions'
    __table_args__ = {'extend_existing':True}
    permission_id = Column("permission_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.permission_id, self.permission_name)

    @classmethod
    def get_by_key(cls, key):
        return cls.query().filter(cls.permission_name == key).scalar()

class UserRepoToPerm(Base, BaseModel):
    __tablename__ = 'repo_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'repository_id'), {'extend_existing':True})
    repo_to_perm_id = Column("repo_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')
    repository = relationship('Repository')

class UserToPerm(Base, BaseModel):
    __tablename__ = 'user_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'permission_id'), {'extend_existing':True})
    user_to_perm_id = Column("user_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')

    @classmethod
    def has_perm(cls, user_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        return cls.query().filter(cls.user_id == user_id)\
            .filter(cls.permission == perm).scalar() is not None

    @classmethod
    def grant_perm(cls, user_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        new = cls()
        new.user_id = user_id
        new.permission = perm
        try:
            Session.add(new)
            Session.commit()
        except:
            Session.rollback()


    @classmethod
    def revoke_perm(cls, user_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        try:
            cls.query().filter(cls.user_id == user_id)\
                .filter(cls.permission == perm).delete()
            Session.commit()
        except:
            Session.rollback()

class UsersGroupRepoToPerm(Base, BaseModel):
    __tablename__ = 'users_group_repo_to_perm'
    __table_args__ = (UniqueConstraint('repository_id', 'users_group_id', 'permission_id'), {'extend_existing':True})
    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UsersGroup')
    permission = relationship('Permission')
    repository = relationship('Repository')

    def __repr__(self):
        return '<userGroup:%s => %s >' % (self.users_group, self.repository)

class UsersGroupToPerm(Base, BaseModel):
    __tablename__ = 'users_group_to_perm'
    __table_args__ = {'extend_existing':True}
    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UsersGroup')
    permission = relationship('Permission')


    @classmethod
    def has_perm(cls, users_group_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        return cls.query().filter(cls.users_group_id ==
                                         users_group_id)\
                                         .filter(cls.permission == perm)\
                                         .scalar() is not None

    @classmethod
    def grant_perm(cls, users_group_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        new = cls()
        new.users_group_id = users_group_id
        new.permission = perm
        try:
            Session.add(new)
            Session.commit()
        except:
            Session.rollback()


    @classmethod
    def revoke_perm(cls, users_group_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        try:
            cls.query().filter(cls.users_group_id == users_group_id)\
                .filter(cls.permission == perm).delete()
            Session.commit()
        except:
            Session.rollback()


class UserRepoGroupToPerm(Base, BaseModel):
    __tablename__ = 'group_to_perm'
    __table_args__ = (UniqueConstraint('group_id', 'permission_id'), {'extend_existing':True})

    group_to_perm_id = Column("group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')
    group = relationship('RepoGroup')

class Statistics(Base, BaseModel):
    __tablename__ = 'statistics'
    __table_args__ = (UniqueConstraint('repository_id'), {'extend_existing':True})
    stat_id = Column("stat_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=True, default=None)
    stat_on_revision = Column("stat_on_revision", Integer(), nullable=False)
    commit_activity = Column("commit_activity", LargeBinary(1000000), nullable=False)#JSON data
    commit_activity_combined = Column("commit_activity_combined", LargeBinary(), nullable=False)#JSON data
    languages = Column("languages", LargeBinary(1000000), nullable=False)#JSON data

    repository = relationship('Repository', single_parent=True)

class UserFollowing(Base, BaseModel):
    __tablename__ = 'user_followings'
    __table_args__ = (UniqueConstraint('user_id', 'follows_repository_id'),
                      UniqueConstraint('user_id', 'follows_user_id')
                      , {'extend_existing':True})

    user_following_id = Column("user_following_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    follows_repo_id = Column("follows_repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=None, default=None)
    follows_user_id = Column("follows_user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    follows_from = Column('follows_from', DateTime(timezone=False), nullable=True, unique=None, default=datetime.datetime.now)

    user = relationship('User', primaryjoin='User.user_id==UserFollowing.user_id')

    follows_user = relationship('User', primaryjoin='User.user_id==UserFollowing.follows_user_id')
    follows_repository = relationship('Repository', order_by='Repository.repo_name')


    @classmethod
    def get_repo_followers(cls, repo_id):
        return cls.query().filter(cls.follows_repo_id == repo_id)

class CacheInvalidation(Base, BaseModel):
    __tablename__ = 'cache_invalidation'
    __table_args__ = (UniqueConstraint('cache_key'), {'extend_existing':True})
    cache_id = Column("cache_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    cache_key = Column("cache_key", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_args = Column("cache_args", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_active = Column("cache_active", Boolean(), nullable=True, unique=None, default=False)


    def __init__(self, cache_key, cache_args=''):
        self.cache_key = cache_key
        self.cache_args = cache_args
        self.cache_active = False

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.cache_id, self.cache_key)

    @classmethod
    def invalidate(cls, key):
        """
        Returns Invalidation object if this given key should be invalidated
        None otherwise. `cache_active = False` means that this cache
        state is not valid and needs to be invalidated

        :param key:
        """
        return cls.query()\
                .filter(CacheInvalidation.cache_key == key)\
                .filter(CacheInvalidation.cache_active == False)\
                .scalar()

    @classmethod
    def set_invalidate(cls, key):
        """
        Mark this Cache key for invalidation

        :param key:
        """

        log.debug('marking %s for invalidation' % key)
        inv_obj = Session.query(cls)\
            .filter(cls.cache_key == key).scalar()
        if inv_obj:
            inv_obj.cache_active = False
        else:
            log.debug('cache key not found in invalidation db -> creating one')
            inv_obj = CacheInvalidation(key)

        try:
            Session.add(inv_obj)
            Session.commit()
        except Exception:
            log.error(traceback.format_exc())
            Session.rollback()

    @classmethod
    def set_valid(cls, key):
        """
        Mark this cache key as active and currently cached

        :param key:
        """
        inv_obj = Session.query(CacheInvalidation)\
            .filter(CacheInvalidation.cache_key == key).scalar()
        inv_obj.cache_active = True
        Session.add(inv_obj)
        Session.commit()

class DbMigrateVersion(Base, BaseModel):
    __tablename__ = 'db_migrate_version'
    __table_args__ = {'extend_existing':True}
    repository_id = Column('repository_id', String(250), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)
