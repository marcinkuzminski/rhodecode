# -*- coding: utf-8 -*-
"""
    rhodecode.model.db_1_4_0
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Database Models for RhodeCode <=1.4.X

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
import hashlib
import time
from collections import defaultdict

from sqlalchemy import *
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, joinedload, class_mapper, validates
from sqlalchemy.exc import DatabaseError
from beaker.cache import cache_region, region_invalidate
from webob.exc import HTTPNotFound

from pylons.i18n.translation import lazy_ugettext as _

from rhodecode.lib.vcs import get_backend
from rhodecode.lib.vcs.utils.helpers import get_scm
from rhodecode.lib.vcs.exceptions import VCSError
from rhodecode.lib.vcs.utils.lazy import LazyProperty

from rhodecode.lib.utils2 import str2bool, safe_str, get_changeset_safe, \
    safe_unicode, remove_suffix
from rhodecode.lib.compat import json
from rhodecode.lib.caching_query import FromCache

from rhodecode.model.meta import Base, Session

URL_SEP = '/'
log = logging.getLogger(__name__)

#==============================================================================
# BASE CLASSES
#==============================================================================

_hash_key = lambda k: hashlib.md5(safe_str(k)).hexdigest()


class BaseModel(object):
    """
    Base Model for all classess
    """

    @classmethod
    def _get_keys(cls):
        """return column names for this model """
        return class_mapper(cls).c.keys()

    def get_dict(self):
        """
        return dict with keys and values corresponding
        to this model data """

        d = {}
        for k in self._get_keys():
            d[k] = getattr(self, k)

        # also use __json__() if present to get additional fields
        _json_attr = getattr(self, '__json__', None)
        if _json_attr:
            # update with attributes from __json__
            if callable(_json_attr):
                _json_attr = _json_attr()
            for k, val in _json_attr.iteritems():
                d[k] = val
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
        return Session().query(cls)

    @classmethod
    def get(cls, id_):
        if id_:
            return cls.query().get(id_)

    @classmethod
    def get_or_404(cls, id_):
        try:
            id_ = int(id_)
        except (TypeError, ValueError):
            raise HTTPNotFound

        res = cls.query().get(id_)
        if not res:
            raise HTTPNotFound
        return res

    @classmethod
    def getAll(cls):
        return cls.query().all()

    @classmethod
    def delete(cls, id_):
        obj = cls.query().get(id_)
        Session().delete(obj)

    def __repr__(self):
        if hasattr(self, '__unicode__'):
            # python repr needs to return str
            return safe_str(self.__unicode__())
        return '<DB:%s>' % (self.__class__.__name__)


class RhodeCodeSetting(Base, BaseModel):
    __tablename__ = 'rhodecode_settings'
    __table_args__ = (
        UniqueConstraint('app_settings_name'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    app_settings_id = Column("app_settings_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    app_settings_name = Column("app_settings_name", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    _app_settings_value = Column("app_settings_value", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

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
        if self.app_settings_name == 'ldap_active':
            v = str2bool(v)
        return v

    @app_settings_value.setter
    def app_settings_value(self, val):
        """
        Setter that will always make sure we use unicode in app_settings_value

        :param val:
        """
        self._app_settings_value = safe_unicode(val)

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (
            self.__class__.__name__,
            self.app_settings_name, self.app_settings_value
        )

    @classmethod
    def get_by_name(cls, key):
        return cls.query()\
            .filter(cls.app_settings_name == key).scalar()

    @classmethod
    def get_by_name_or_create(cls, key):
        res = cls.get_by_name(key)
        if not res:
            res = cls(key)
        return res

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
            fd.update({row.app_settings_name: row.app_settings_value})

        return fd


class RhodeCodeUi(Base, BaseModel):
    __tablename__ = 'rhodecode_ui'
    __table_args__ = (
        UniqueConstraint('ui_key'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )

    HOOK_UPDATE = 'changegroup.update'
    HOOK_REPO_SIZE = 'changegroup.repo_size'
    HOOK_PUSH = 'changegroup.push_logger'
    HOOK_PRE_PUSH = 'prechangegroup.pre_push'
    HOOK_PULL = 'outgoing.pull_logger'
    HOOK_PRE_PULL = 'preoutgoing.pre_pull'

    ui_id = Column("ui_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    ui_section = Column("ui_section", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_key = Column("ui_key", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_value = Column("ui_value", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_active = Column("ui_active", Boolean(), nullable=True, unique=None, default=True)

    @classmethod
    def get_by_key(cls, key):
        return cls.query().filter(cls.ui_key == key).scalar()

    @classmethod
    def get_builtin_hooks(cls):
        q = cls.query()
        q = q.filter(cls.ui_key.in_([cls.HOOK_UPDATE, cls.HOOK_REPO_SIZE,
                                     cls.HOOK_PUSH, cls.HOOK_PRE_PUSH,
                                     cls.HOOK_PULL, cls.HOOK_PRE_PULL]))
        return q.all()

    @classmethod
    def get_custom_hooks(cls):
        q = cls.query()
        q = q.filter(~cls.ui_key.in_([cls.HOOK_UPDATE, cls.HOOK_REPO_SIZE,
                                      cls.HOOK_PUSH, cls.HOOK_PRE_PUSH,
                                      cls.HOOK_PULL, cls.HOOK_PRE_PULL]))
        q = q.filter(cls.ui_section == 'hooks')
        return q.all()

    @classmethod
    def get_repos_location(cls):
        return cls.get_by_key('/').ui_value

    @classmethod
    def create_or_update_hook(cls, key, val):
        new_ui = cls.get_by_key(key) or cls()
        new_ui.ui_section = 'hooks'
        new_ui.ui_active = True
        new_ui.ui_key = key
        new_ui.ui_value = val

        Session().add(new_ui)

    def __repr__(self):
        return '<DB:%s[%s:%s]>' % (self.__class__.__name__, self.ui_key,
                                   self.ui_value)


class User(Base, BaseModel):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('username'), UniqueConstraint('email'),
        Index('u_username_idx', 'username'),
        Index('u_email_idx', 'email'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    DEFAULT_USER = 'default'
    DEFAULT_PERMISSIONS = [
        'hg.register.manual_activate', 'hg.create.repository',
        'hg.fork.repository', 'repository.read', 'group.read'
    ]
    user_id = Column("user_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    username = Column("username", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", Boolean(), nullable=True, unique=None, default=True)
    admin = Column("admin", Boolean(), nullable=True, unique=None, default=False)
    name = Column("firstname", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    lastname = Column("lastname", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    _email = Column("email", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    last_login = Column("last_login", DateTime(timezone=False), nullable=True, unique=None, default=None)
    ldap_dn = Column("ldap_dn", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    api_key = Column("api_key", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    inherit_default_permissions = Column("inherit_default_permissions", Boolean(), nullable=False, unique=None, default=True)

    user_log = relationship('UserLog', cascade='all')
    user_perms = relationship('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all')

    repositories = relationship('Repository')
    user_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')
    repo_to_perm = relationship('UserRepoToPerm', primaryjoin='UserRepoToPerm.user_id==User.user_id', cascade='all')
    repo_group_to_perm = relationship('UserRepoGroupToPerm', primaryjoin='UserRepoGroupToPerm.user_id==User.user_id', cascade='all')

    group_member = relationship('UserGroupMember', cascade='all')

    notifications = relationship('UserNotification', cascade='all')
    # notifications assigned to this user
    user_created_notifications = relationship('Notification', cascade='all')
    # comments created by this user
    user_comments = relationship('ChangesetComment', cascade='all')
    #extra emails for this user
    user_emails = relationship('UserEmailMap', cascade='all')

    @hybrid_property
    def email(self):
        return self._email

    @email.setter
    def email(self, val):
        self._email = val.lower() if val else None

    @property
    def firstname(self):
        # alias for future
        return self.name

    @property
    def emails(self):
        other = UserEmailMap.query().filter(UserEmailMap.user==self).all()
        return [self.email] + [x.email for x in other]

    @property
    def username_and_name(self):
        return '%s (%s %s)' % (self.username, self.firstname, self.lastname)

    @property
    def full_name(self):
        return '%s %s' % (self.firstname, self.lastname)

    @property
    def full_name_or_username(self):
        return ('%s %s' % (self.firstname, self.lastname)
                if (self.firstname and self.lastname) else self.username)

    @property
    def full_contact(self):
        return '%s %s <%s>' % (self.firstname, self.lastname, self.email)

    @property
    def short_contact(self):
        return '%s %s' % (self.firstname, self.lastname)

    @property
    def is_admin(self):
        return self.admin

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (self.__class__.__name__,
                                     self.user_id, self.username)

    @classmethod
    def get_by_username(cls, username, case_insensitive=False, cache=False):
        if case_insensitive:
            q = cls.query().filter(cls.username.ilike(username))
        else:
            q = cls.query().filter(cls.username == username)

        if cache:
            q = q.options(FromCache(
                            "sql_cache_short",
                            "get_user_%s" % _hash_key(username)
                          )
            )
        return q.scalar()

    @classmethod
    def get_by_api_key(cls, api_key, cache=False):
        q = cls.query().filter(cls.api_key == api_key)

        if cache:
            q = q.options(FromCache("sql_cache_short",
                                    "get_api_key_%s" % api_key))
        return q.scalar()

    @classmethod
    def get_by_email(cls, email, case_insensitive=False, cache=False):
        if case_insensitive:
            q = cls.query().filter(cls.email.ilike(email))
        else:
            q = cls.query().filter(cls.email == email)

        if cache:
            q = q.options(FromCache("sql_cache_short",
                                    "get_email_key_%s" % email))

        ret = q.scalar()
        if ret is None:
            q = UserEmailMap.query()
            # try fetching in alternate email map
            if case_insensitive:
                q = q.filter(UserEmailMap.email.ilike(email))
            else:
                q = q.filter(UserEmailMap.email == email)
            q = q.options(joinedload(UserEmailMap.user))
            if cache:
                q = q.options(FromCache("sql_cache_short",
                                        "get_email_map_key_%s" % email))
            ret = getattr(q.scalar(), 'user', None)

        return ret

    def update_lastlogin(self):
        """Update user lastlogin"""
        self.last_login = datetime.datetime.now()
        Session().add(self)
        log.debug('updated user %s lastlogin' % self.username)

    def get_api_data(self):
        """
        Common function for generating user related data for API
        """
        user = self
        data = dict(
            user_id=user.user_id,
            username=user.username,
            firstname=user.name,
            lastname=user.lastname,
            email=user.email,
            emails=user.emails,
            api_key=user.api_key,
            active=user.active,
            admin=user.admin,
            ldap_dn=user.ldap_dn,
            last_login=user.last_login,
        )
        return data

    def __json__(self):
        data = dict(
            full_name=self.full_name,
            full_name_or_username=self.full_name_or_username,
            short_contact=self.short_contact,
            full_contact=self.full_contact
        )
        data.update(self.get_api_data())
        return data


class UserEmailMap(Base, BaseModel):
    __tablename__ = 'user_email_map'
    __table_args__ = (
        Index('uem_email_idx', 'email'),
        UniqueConstraint('email'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    __mapper_args__ = {}

    email_id = Column("email_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    _email = Column("email", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=False, default=None)
    user = relationship('User', lazy='joined')

    @validates('_email')
    def validate_email(self, key, email):
        # check if this email is not main one
        main_email = Session().query(User).filter(User.email == email).scalar()
        if main_email is not None:
            raise AttributeError('email %s is present is user table' % email)
        return email

    @hybrid_property
    def email(self):
        return self._email

    @email.setter
    def email(self, val):
        self._email = val.lower() if val else None


class UserLog(Base, BaseModel):
    __tablename__ = 'user_logs'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    user_log_id = Column("user_log_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True)
    repository_name = Column("repository_name", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    user_ip = Column("user_ip", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", UnicodeText(1200000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DateTime(timezone=False), nullable=True, unique=None, default=None)

    @property
    def action_as_day(self):
        return datetime.date(*self.action_date.timetuple()[:3])

    user = relationship('User')
    repository = relationship('Repository', cascade='')


class UserGroup(Base, BaseModel):
    __tablename__ = 'users_groups'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )

    users_group_id = Column("users_group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_name = Column("users_group_name", String(255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    users_group_active = Column("users_group_active", Boolean(), nullable=True, unique=None, default=None)
    inherit_default_permissions = Column("users_group_inherit_default_permissions", Boolean(), nullable=False, unique=None, default=True)

    members = relationship('UserGroupMember', cascade="all, delete, delete-orphan", lazy="joined")
    users_group_to_perm = relationship('UserGroupToPerm', cascade='all')
    users_group_repo_to_perm = relationship('UserGroupRepoToPerm', cascade='all')

    def __unicode__(self):
        return u'<userGroup(%s)>' % (self.users_group_name)

    @classmethod
    def get_by_group_name(cls, group_name, cache=False,
                          case_insensitive=False):
        if case_insensitive:
            q = cls.query().filter(cls.users_group_name.ilike(group_name))
        else:
            q = cls.query().filter(cls.users_group_name == group_name)
        if cache:
            q = q.options(FromCache(
                            "sql_cache_short",
                            "get_user_%s" % _hash_key(group_name)
                          )
            )
        return q.scalar()

    @classmethod
    def get(cls, users_group_id, cache=False):
        users_group = cls.query()
        if cache:
            users_group = users_group.options(FromCache("sql_cache_short",
                                    "get_users_group_%s" % users_group_id))
        return users_group.get(users_group_id)

    def get_api_data(self):
        users_group = self

        data = dict(
            users_group_id=users_group.users_group_id,
            group_name=users_group.users_group_name,
            active=users_group.users_group_active,
        )

        return data


class UserGroupMember(Base, BaseModel):
    __tablename__ = 'users_groups_members'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )

    users_group_member_id = Column("users_group_member_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)

    user = relationship('User', lazy='joined')
    users_group = relationship('UserGroup')

    def __init__(self, gr_id='', u_id=''):
        self.users_group_id = gr_id
        self.user_id = u_id


class Repository(Base, BaseModel):
    __tablename__ = 'repositories'
    __table_args__ = (
        UniqueConstraint('repo_name'),
        Index('r_repo_name_idx', 'repo_name'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )

    repo_id = Column("repo_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repo_name = Column("repo_name", String(255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    clone_uri = Column("clone_uri", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=False, default=None)
    repo_type = Column("repo_type", String(255, convert_unicode=False, assert_unicode=None), nullable=False, unique=False, default=None)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", Boolean(), nullable=True, unique=None, default=None)
    enable_statistics = Column("statistics", Boolean(), nullable=True, unique=None, default=True)
    enable_downloads = Column("downloads", Boolean(), nullable=True, unique=None, default=True)
    description = Column("description", String(10000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    created_on = Column('created_on', DateTime(timezone=False), nullable=True, unique=None, default=datetime.datetime.now)
    updated_on = Column('updated_on', DateTime(timezone=False), nullable=True, unique=None, default=datetime.datetime.now)
    landing_rev = Column("landing_revision", String(255, convert_unicode=False, assert_unicode=None), nullable=False, unique=False, default=None)
    enable_locking = Column("enable_locking", Boolean(), nullable=False, unique=None, default=False)
    _locked = Column("locked", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=False, default=None)

    fork_id = Column("fork_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=False, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=False, default=None)

    user = relationship('User')
    fork = relationship('Repository', remote_side=repo_id)
    group = relationship('RepoGroup')
    repo_to_perm = relationship('UserRepoToPerm', cascade='all', order_by='UserRepoToPerm.repo_to_perm_id')
    users_group_to_perm = relationship('UserGroupRepoToPerm', cascade='all')
    stats = relationship('Statistics', cascade='all', uselist=False)

    followers = relationship('UserFollowing',
                             primaryjoin='UserFollowing.follows_repo_id==Repository.repo_id',
                             cascade='all')

    logs = relationship('UserLog')
    comments = relationship('ChangesetComment', cascade="all, delete, delete-orphan")

    pull_requests_org = relationship('PullRequest',
                    primaryjoin='PullRequest.org_repo_id==Repository.repo_id',
                    cascade="all, delete, delete-orphan")

    pull_requests_other = relationship('PullRequest',
                    primaryjoin='PullRequest.other_repo_id==Repository.repo_id',
                    cascade="all, delete, delete-orphan")

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (self.__class__.__name__, self.repo_id,
                                   self.repo_name)

    @hybrid_property
    def locked(self):
        # always should return [user_id, timelocked]
        if self._locked:
            _lock_info = self._locked.split(':')
            return int(_lock_info[0]), _lock_info[1]
        return [None, None]

    @locked.setter
    def locked(self, val):
        if val and isinstance(val, (list, tuple)):
            self._locked = ':'.join(map(str, val))
        else:
            self._locked = None

    @classmethod
    def url_sep(cls):
        return URL_SEP

    @classmethod
    def get_by_repo_name(cls, repo_name):
        q = Session().query(cls).filter(cls.repo_name == repo_name)
        q = q.options(joinedload(Repository.fork))\
                .options(joinedload(Repository.user))\
                .options(joinedload(Repository.group))
        return q.scalar()

    @classmethod
    def get_by_full_path(cls, repo_full_path):
        repo_name = repo_full_path.split(cls.base_path(), 1)[-1]
        return cls.get_by_repo_name(repo_name.strip(URL_SEP))

    @classmethod
    def get_repo_forks(cls, repo_id):
        return cls.query().filter(Repository.fork_id == repo_id)

    @classmethod
    def base_path(cls):
        """
        Returns base path when all repos are stored

        :param cls:
        """
        q = Session().query(RhodeCodeUi)\
            .filter(RhodeCodeUi.ui_key == cls.url_sep())
        q = q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return q.one().ui_value

    @property
    def forks(self):
        """
        Return forks of this repo
        """
        return Repository.get_repo_forks(self.repo_id)

    @property
    def parent(self):
        """
        Returns fork parent
        """
        return self.fork

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
        q = Session().query(RhodeCodeUi).filter(RhodeCodeUi.ui_key ==
                                              Repository.url_sep())
        q = q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return q.one().ui_value

    @property
    def repo_full_path(self):
        p = [self.repo_path]
        # we need to split the name by / since this is how we store the
        # names in the database, but that eventually needs to be converted
        # into a valid system path
        p += self.repo_name.split(Repository.url_sep())
        return os.path.join(*p)

    @property
    def cache_keys(self):
        """
        Returns associated cache keys for that repo
        """
        return CacheInvalidation.query()\
            .filter(CacheInvalidation.cache_args == self.repo_name)\
            .order_by(CacheInvalidation.cache_key)\
            .all()

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
        from rhodecode.lib.utils import make_ui
        return make_ui('db', clear_session=False)

    @classmethod
    def inject_ui(cls, repo, extras={}):
        from rhodecode.lib.vcs.backends.hg import MercurialRepository
        from rhodecode.lib.vcs.backends.git import GitRepository
        required = (MercurialRepository, GitRepository)
        if not isinstance(repo, required):
            raise Exception('repo must be instance of %s' % (','.join(required)))

        # inject ui extra param to log this action via push logger
        for k, v in extras.items():
            repo._repo.ui.setconfig('rhodecode_extras', k, v)

    @classmethod
    def is_valid(cls, repo_name):
        """
        returns True if given repo name is a valid filesystem repository

        :param cls:
        :param repo_name:
        """
        from rhodecode.lib.utils import is_valid_repo

        return is_valid_repo(repo_name, cls.base_path())

    def get_api_data(self):
        """
        Common function for generating repo api data

        """
        repo = self
        data = dict(
            repo_id=repo.repo_id,
            repo_name=repo.repo_name,
            repo_type=repo.repo_type,
            clone_uri=repo.clone_uri,
            private=repo.private,
            created_on=repo.created_on,
            description=repo.description,
            landing_rev=repo.landing_rev,
            owner=repo.user.username,
            fork_of=repo.fork.repo_name if repo.fork else None
        )

        return data

    @classmethod
    def lock(cls, repo, user_id):
        repo.locked = [user_id, time.time()]
        Session().add(repo)
        Session().commit()

    @classmethod
    def unlock(cls, repo):
        repo.locked = None
        Session().add(repo)
        Session().commit()

    @property
    def last_db_change(self):
        return self.updated_on

    #==========================================================================
    # SCM PROPERTIES
    #==========================================================================

    def get_changeset(self, rev=None):
        return get_changeset_safe(self.scm_instance, rev)

    def get_landing_changeset(self):
        """
        Returns landing changeset, or if that doesn't exist returns the tip
        """
        cs = self.get_changeset(self.landing_rev) or self.get_changeset()
        return cs

    def update_last_change(self, last_change=None):
        if last_change is None:
            last_change = datetime.datetime.now()
        if self.updated_on is None or self.updated_on != last_change:
            log.debug('updated repo %s with new date %s' % (self, last_change))
            self.updated_on = last_change
            Session().add(self)
            Session().commit()

    @property
    def tip(self):
        return self.get_changeset('tip')

    @property
    def author(self):
        return self.tip.author

    @property
    def last_change(self):
        return self.scm_instance.last_change

    def get_comments(self, revisions=None):
        """
        Returns comments for this repository grouped by revisions

        :param revisions: filter query by revisions only
        """
        cmts = ChangesetComment.query()\
            .filter(ChangesetComment.repo == self)
        if revisions:
            cmts = cmts.filter(ChangesetComment.revision.in_(revisions))
        grouped = defaultdict(list)
        for cmt in cmts.all():
            grouped[cmt.revision].append(cmt)
        return grouped

    def statuses(self, revisions=None):
        """
        Returns statuses for this repository

        :param revisions: list of revisions to get statuses for
        :type revisions: list
        """

        statuses = ChangesetStatus.query()\
            .filter(ChangesetStatus.repo == self)\
            .filter(ChangesetStatus.version == 0)
        if revisions:
            statuses = statuses.filter(ChangesetStatus.revision.in_(revisions))
        grouped = {}

        #maybe we have open new pullrequest without a status ?
        stat = ChangesetStatus.STATUS_UNDER_REVIEW
        status_lbl = ChangesetStatus.get_status_lbl(stat)
        for pr in PullRequest.query().filter(PullRequest.org_repo == self).all():
            for rev in pr.revisions:
                pr_id = pr.pull_request_id
                pr_repo = pr.other_repo.repo_name
                grouped[rev] = [stat, status_lbl, pr_id, pr_repo]

        for stat in statuses.all():
            pr_id = pr_repo = None
            if stat.pull_request:
                pr_id = stat.pull_request.pull_request_id
                pr_repo = stat.pull_request.other_repo.repo_name
            grouped[stat.revision] = [str(stat.status), stat.status_lbl,
                                      pr_id, pr_repo]
        return grouped

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
        CacheInvalidation.set_invalidate(repo_name=self.repo_name)

    @LazyProperty
    def scm_instance(self):
        import rhodecode
        full_cache = str2bool(rhodecode.CONFIG.get('vcs_full_cache'))
        if full_cache:
            return self.scm_instance_cached()
        return self.__get_instance()

    def scm_instance_cached(self, cache_map=None):
        @cache_region('long_term')
        def _c(repo_name):
            return self.__get_instance()
        rn = self.repo_name
        log.debug('Getting cached instance of repo')

        if cache_map:
            # get using prefilled cache_map
            invalidate_repo = cache_map[self.repo_name]
            if invalidate_repo:
                invalidate_repo = (None if invalidate_repo.cache_active
                                   else invalidate_repo)
        else:
            # get from invalidate
            invalidate_repo = self.invalidate

        if invalidate_repo is not None:
            region_invalidate(_c, None, rn)
            # update our cache
            CacheInvalidation.set_valid(invalidate_repo.cache_key)
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
    __table_args__ = (
        UniqueConstraint('group_name', 'group_parent_id'),
        CheckConstraint('group_id != group_parent_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    __mapper_args__ = {'order_by': 'group_name'}

    group_id = Column("group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    group_name = Column("group_name", String(255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    group_parent_id = Column("group_parent_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=None, default=None)
    group_description = Column("group_description", String(10000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    enable_locking = Column("enable_locking", Boolean(), nullable=False, unique=None, default=False)

    repo_group_to_perm = relationship('UserRepoGroupToPerm', cascade='all', order_by='UserRepoGroupToPerm.group_to_perm_id')
    users_group_to_perm = relationship('UserGroupRepoGroupToPerm', cascade='all')

    parent_group = relationship('RepoGroup', remote_side=group_id)

    def __init__(self, group_name='', parent_group=None):
        self.group_name = group_name
        self.parent_group = parent_group

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (self.__class__.__name__, self.group_id,
                                  self.group_name)

    @classmethod
    def groups_choices(cls, check_perms=False):
        from webhelpers.html import literal as _literal
        from rhodecode.model.scm import ScmModel
        groups = cls.query().all()
        if check_perms:
            #filter group user have access to, it's done
            #magically inside ScmModel based on current user
            groups = ScmModel().get_repos_groups(groups)
        repo_groups = [('', '')]
        sep = ' &raquo; '
        _name = lambda k: _literal(sep.join(k))

        repo_groups.extend([(x.group_id, _name(x.full_path_splitted))
                              for x in groups])

        repo_groups = sorted(repo_groups, key=lambda t: t[1].split(sep)[0])
        return repo_groups

    @classmethod
    def url_sep(cls):
        return URL_SEP

    @classmethod
    def get_by_group_name(cls, group_name, cache=False, case_insensitive=False):
        if case_insensitive:
            gr = cls.query()\
                .filter(cls.group_name.ilike(group_name))
        else:
            gr = cls.query()\
                .filter(cls.group_name == group_name)
        if cache:
            gr = gr.options(FromCache(
                            "sql_cache_short",
                            "get_group_%s" % _hash_key(group_name)
                            )
            )
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
        return RepoGroup.query().filter(RepoGroup.parent_group == self)

    @property
    def name(self):
        return self.group_name.split(RepoGroup.url_sep())[-1]

    @property
    def full_path(self):
        return self.group_name

    @property
    def full_path_splitted(self):
        return self.group_name.split(RepoGroup.url_sep())

    @property
    def repositories(self):
        return Repository.query()\
                .filter(Repository.group == self)\
                .order_by(Repository.repo_name)

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

    def recursive_groups_and_repos(self):
        """
        Recursive return all groups, with repositories in those groups
        """
        all_ = []

        def _get_members(root_gr):
            for r in root_gr.repositories:
                all_.append(r)
            childs = root_gr.children.all()
            if childs:
                for gr in childs:
                    all_.append(gr)
                    _get_members(gr)

        _get_members(self)
        return [self] + all_

    def get_new_name(self, group_name):
        """
        returns new full group name based on parent and new name

        :param group_name:
        """
        path_prefix = (self.parent_group.full_path_splitted if
                       self.parent_group else [])
        return RepoGroup.url_sep().join(path_prefix + [group_name])


class Permission(Base, BaseModel):
    __tablename__ = 'permissions'
    __table_args__ = (
        Index('p_perm_name_idx', 'permission_name'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    PERMS = [
        ('repository.none', _('Repository no access')),
        ('repository.read', _('Repository read access')),
        ('repository.write', _('Repository write access')),
        ('repository.admin', _('Repository admin access')),

        ('group.none', _('Repositories Group no access')),
        ('group.read', _('Repositories Group read access')),
        ('group.write', _('Repositories Group write access')),
        ('group.admin', _('Repositories Group admin access')),

        ('hg.admin', _('RhodeCode Administrator')),
        ('hg.create.none', _('Repository creation disabled')),
        ('hg.create.repository', _('Repository creation enabled')),
        ('hg.fork.none', _('Repository forking disabled')),
        ('hg.fork.repository', _('Repository forking enabled')),
        ('hg.register.none', _('Register disabled')),
        ('hg.register.manual_activate', _('Register new user with RhodeCode '
                                          'with manual activation')),

        ('hg.register.auto_activate', _('Register new user with RhodeCode '
                                        'with auto activation')),
    ]

    # defines which permissions are more important higher the more important
    PERM_WEIGHTS = {
        'repository.none': 0,
        'repository.read': 1,
        'repository.write': 3,
        'repository.admin': 4,

        'group.none': 0,
        'group.read': 1,
        'group.write': 3,
        'group.admin': 4,

        'hg.fork.none': 0,
        'hg.fork.repository': 1,
        'hg.create.none': 0,
        'hg.create.repository':1
    }

    permission_id = Column("permission_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (
            self.__class__.__name__, self.permission_id, self.permission_name
        )

    @classmethod
    def get_by_key(cls, key):
        return cls.query().filter(cls.permission_name == key).scalar()

    @classmethod
    def get_default_perms(cls, default_user_id):
        q = Session().query(UserRepoToPerm, Repository, cls)\
         .join((Repository, UserRepoToPerm.repository_id == Repository.repo_id))\
         .join((cls, UserRepoToPerm.permission_id == cls.permission_id))\
         .filter(UserRepoToPerm.user_id == default_user_id)

        return q.all()

    @classmethod
    def get_default_group_perms(cls, default_user_id):
        q = Session().query(UserRepoGroupToPerm, RepoGroup, cls)\
         .join((RepoGroup, UserRepoGroupToPerm.group_id == RepoGroup.group_id))\
         .join((cls, UserRepoGroupToPerm.permission_id == cls.permission_id))\
         .filter(UserRepoGroupToPerm.user_id == default_user_id)

        return q.all()


class UserRepoToPerm(Base, BaseModel):
    __tablename__ = 'repo_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'repository_id', 'permission_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    repo_to_perm_id = Column("repo_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    repository = relationship('Repository')
    permission = relationship('Permission')

    @classmethod
    def create(cls, user, repository, permission):
        n = cls()
        n.user = user
        n.repository = repository
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<user:%s => %s >' % (self.user, self.repository)


class UserToPerm(Base, BaseModel):
    __tablename__ = 'user_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'permission_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    user_to_perm_id = Column("user_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission', lazy='joined')


class UserGroupRepoToPerm(Base, BaseModel):
    __tablename__ = 'users_group_repo_to_perm'
    __table_args__ = (
        UniqueConstraint('repository_id', 'users_group_id', 'permission_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UserGroup')
    permission = relationship('Permission')
    repository = relationship('Repository')

    @classmethod
    def create(cls, users_group, repository, permission):
        n = cls()
        n.users_group = users_group
        n.repository = repository
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<userGroup:%s => %s >' % (self.users_group, self.repository)


class UserGroupToPerm(Base, BaseModel):
    __tablename__ = 'users_group_to_perm'
    __table_args__ = (
        UniqueConstraint('users_group_id', 'permission_id',),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UserGroup')
    permission = relationship('Permission')


class UserRepoGroupToPerm(Base, BaseModel):
    __tablename__ = 'user_repo_group_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', 'permission_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )

    group_to_perm_id = Column("group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    group = relationship('RepoGroup')
    permission = relationship('Permission')


class UserGroupRepoGroupToPerm(Base, BaseModel):
    __tablename__ = 'users_group_repo_group_to_perm'
    __table_args__ = (
        UniqueConstraint('users_group_id', 'group_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )

    users_group_repo_group_to_perm_id = Column("users_group_repo_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UserGroup')
    permission = relationship('Permission')
    group = relationship('RepoGroup')


class Statistics(Base, BaseModel):
    __tablename__ = 'statistics'
    __table_args__ = (
         UniqueConstraint('repository_id'),
         {'extend_existing': True, 'mysql_engine': 'InnoDB',
          'mysql_charset': 'utf8'}
    )
    stat_id = Column("stat_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=True, default=None)
    stat_on_revision = Column("stat_on_revision", Integer(), nullable=False)
    commit_activity = Column("commit_activity", LargeBinary(1000000), nullable=False)#JSON data
    commit_activity_combined = Column("commit_activity_combined", LargeBinary(), nullable=False)#JSON data
    languages = Column("languages", LargeBinary(1000000), nullable=False)#JSON data

    repository = relationship('Repository', single_parent=True)


class UserFollowing(Base, BaseModel):
    __tablename__ = 'user_followings'
    __table_args__ = (
        UniqueConstraint('user_id', 'follows_repository_id'),
        UniqueConstraint('user_id', 'follows_user_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )

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
    __table_args__ = (
        UniqueConstraint('cache_key'),
        Index('key_idx', 'cache_key'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    cache_id = Column("cache_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    cache_key = Column("cache_key", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_args = Column("cache_args", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_active = Column("cache_active", Boolean(), nullable=True, unique=None, default=False)

    def __init__(self, cache_key, cache_args=''):
        self.cache_key = cache_key
        self.cache_args = cache_args
        self.cache_active = False

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.cache_id, self.cache_key)

    @property
    def prefix(self):
        _split = self.cache_key.split(self.cache_args, 1)
        if _split and len(_split) == 2:
            return _split[0]
        return ''

    @classmethod
    def clear_cache(cls):
        cls.query().delete()

    @classmethod
    def _get_key(cls, key):
        """
        Wrapper for generating a key, together with a prefix

        :param key:
        """
        import rhodecode
        prefix = ''
        org_key = key
        iid = rhodecode.CONFIG.get('instance_id')
        if iid:
            prefix = iid

        return "%s%s" % (prefix, key), prefix, org_key

    @classmethod
    def get_by_key(cls, key):
        return cls.query().filter(cls.cache_key == key).scalar()

    @classmethod
    def get_by_repo_name(cls, repo_name):
        return cls.query().filter(cls.cache_args == repo_name).all()

    @classmethod
    def _get_or_create_key(cls, key, repo_name, commit=True):
        inv_obj = Session().query(cls).filter(cls.cache_key == key).scalar()
        if not inv_obj:
            try:
                inv_obj = CacheInvalidation(key, repo_name)
                Session().add(inv_obj)
                if commit:
                    Session().commit()
            except Exception:
                log.error(traceback.format_exc())
                Session().rollback()
        return inv_obj

    @classmethod
    def invalidate(cls, key):
        """
        Returns Invalidation object if this given key should be invalidated
        None otherwise. `cache_active = False` means that this cache
        state is not valid and needs to be invalidated

        :param key:
        """
        repo_name = key
        repo_name = remove_suffix(repo_name, '_README')
        repo_name = remove_suffix(repo_name, '_RSS')
        repo_name = remove_suffix(repo_name, '_ATOM')

        # adds instance prefix
        key, _prefix, _org_key = cls._get_key(key)
        inv = cls._get_or_create_key(key, repo_name)

        if inv and inv.cache_active is False:
            return inv

    @classmethod
    def set_invalidate(cls, key=None, repo_name=None):
        """
        Mark this Cache key for invalidation, either by key or whole
        cache sets based on repo_name

        :param key:
        """
        if key:
            key, _prefix, _org_key = cls._get_key(key)
            inv_objs = Session().query(cls).filter(cls.cache_key == key).all()
        elif repo_name:
            inv_objs = Session().query(cls).filter(cls.cache_args == repo_name).all()

        log.debug('marking %s key[s] for invalidation based on key=%s,repo_name=%s'
                  % (len(inv_objs), key, repo_name))
        try:
            for inv_obj in inv_objs:
                inv_obj.cache_active = False
                Session().add(inv_obj)
            Session().commit()
        except Exception:
            log.error(traceback.format_exc())
            Session().rollback()

    @classmethod
    def set_valid(cls, key):
        """
        Mark this cache key as active and currently cached

        :param key:
        """
        inv_obj = cls.get_by_key(key)
        inv_obj.cache_active = True
        Session().add(inv_obj)
        Session().commit()

    @classmethod
    def get_cache_map(cls):

        class cachemapdict(dict):

            def __init__(self, *args, **kwargs):
                fixkey = kwargs.get('fixkey')
                if fixkey:
                    del kwargs['fixkey']
                self.fixkey = fixkey
                super(cachemapdict, self).__init__(*args, **kwargs)

            def __getattr__(self, name):
                key = name
                if self.fixkey:
                    key, _prefix, _org_key = cls._get_key(key)
                if key in self.__dict__:
                    return self.__dict__[key]
                else:
                    return self[key]

            def __getitem__(self, key):
                if self.fixkey:
                    key, _prefix, _org_key = cls._get_key(key)
                try:
                    return super(cachemapdict, self).__getitem__(key)
                except KeyError:
                    return

        cache_map = cachemapdict(fixkey=True)
        for obj in cls.query().all():
            cache_map[obj.cache_key] = cachemapdict(obj.get_dict())
        return cache_map


class ChangesetComment(Base, BaseModel):
    __tablename__ = 'changeset_comments'
    __table_args__ = (
        Index('cc_revision_idx', 'revision'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    comment_id = Column('comment_id', Integer(), nullable=False, primary_key=True)
    repo_id = Column('repo_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False)
    revision = Column('revision', String(40), nullable=True)
    pull_request_id = Column("pull_request_id", Integer(), ForeignKey('pull_requests.pull_request_id'), nullable=True)
    line_no = Column('line_no', Unicode(10), nullable=True)
    hl_lines = Column('hl_lines', Unicode(512), nullable=True)
    f_path = Column('f_path', Unicode(1000), nullable=True)
    user_id = Column('user_id', Integer(), ForeignKey('users.user_id'), nullable=False)
    text = Column('text', UnicodeText(25000), nullable=False)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    modified_at = Column('modified_at', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)

    author = relationship('User', lazy='joined')
    repo = relationship('Repository')
    status_change = relationship('ChangesetStatus', cascade="all, delete, delete-orphan")
    pull_request = relationship('PullRequest', lazy='joined')

    @classmethod
    def get_users(cls, revision=None, pull_request_id=None):
        """
        Returns user associated with this ChangesetComment. ie those
        who actually commented

        :param cls:
        :param revision:
        """
        q = Session().query(User)\
                .join(ChangesetComment.author)
        if revision:
            q = q.filter(cls.revision == revision)
        elif pull_request_id:
            q = q.filter(cls.pull_request_id == pull_request_id)
        return q.all()


class ChangesetStatus(Base, BaseModel):
    __tablename__ = 'changeset_statuses'
    __table_args__ = (
        Index('cs_revision_idx', 'revision'),
        Index('cs_version_idx', 'version'),
        UniqueConstraint('repo_id', 'revision', 'version'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    STATUS_NOT_REVIEWED = DEFAULT = 'not_reviewed'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_UNDER_REVIEW = 'under_review'

    STATUSES = [
        (STATUS_NOT_REVIEWED, _("Not Reviewed")),  # (no icon) and default
        (STATUS_APPROVED, _("Approved")),
        (STATUS_REJECTED, _("Rejected")),
        (STATUS_UNDER_REVIEW, _("Under Review")),
    ]

    changeset_status_id = Column('changeset_status_id', Integer(), nullable=False, primary_key=True)
    repo_id = Column('repo_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None)
    revision = Column('revision', String(40), nullable=False)
    status = Column('status', String(128), nullable=False, default=DEFAULT)
    changeset_comment_id = Column('changeset_comment_id', Integer(), ForeignKey('changeset_comments.comment_id'))
    modified_at = Column('modified_at', DateTime(), nullable=False, default=datetime.datetime.now)
    version = Column('version', Integer(), nullable=False, default=0)
    pull_request_id = Column("pull_request_id", Integer(), ForeignKey('pull_requests.pull_request_id'), nullable=True)

    author = relationship('User', lazy='joined')
    repo = relationship('Repository')
    comment = relationship('ChangesetComment', lazy='joined')
    pull_request = relationship('PullRequest', lazy='joined')

    def __unicode__(self):
        return u"<%s('%s:%s')>" % (
            self.__class__.__name__,
            self.status, self.author
        )

    @classmethod
    def get_status_lbl(cls, value):
        return dict(cls.STATUSES).get(value)

    @property
    def status_lbl(self):
        return ChangesetStatus.get_status_lbl(self.status)


class PullRequest(Base, BaseModel):
    __tablename__ = 'pull_requests'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )

    STATUS_NEW = u'new'
    STATUS_OPEN = u'open'
    STATUS_CLOSED = u'closed'

    pull_request_id = Column('pull_request_id', Integer(), nullable=False, primary_key=True)
    title = Column('title', Unicode(256), nullable=True)
    description = Column('description', UnicodeText(10240), nullable=True)
    status = Column('status', Unicode(256), nullable=False, default=STATUS_NEW)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    updated_on = Column('updated_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None)
    _revisions = Column('revisions', UnicodeText(20500))  # 500 revisions max
    org_repo_id = Column('org_repo_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False)
    org_ref = Column('org_ref', Unicode(256), nullable=False)
    other_repo_id = Column('other_repo_id', Integer(), ForeignKey('repositories.repo_id'), nullable=False)
    other_ref = Column('other_ref', Unicode(256), nullable=False)

    @hybrid_property
    def revisions(self):
        return self._revisions.split(':')

    @revisions.setter
    def revisions(self, val):
        self._revisions = ':'.join(val)

    author = relationship('User', lazy='joined')
    reviewers = relationship('PullRequestReviewers',
                             cascade="all, delete, delete-orphan")
    org_repo = relationship('Repository', primaryjoin='PullRequest.org_repo_id==Repository.repo_id')
    other_repo = relationship('Repository', primaryjoin='PullRequest.other_repo_id==Repository.repo_id')
    statuses = relationship('ChangesetStatus')
    comments = relationship('ChangesetComment',
                             cascade="all, delete, delete-orphan")

    def is_closed(self):
        return self.status == self.STATUS_CLOSED

    def __json__(self):
        return dict(
          revisions=self.revisions
        )


class PullRequestReviewers(Base, BaseModel):
    __tablename__ = 'pull_request_reviewers'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )

    def __init__(self, user=None, pull_request=None):
        self.user = user
        self.pull_request = pull_request

    pull_requests_reviewers_id = Column('pull_requests_reviewers_id', Integer(), nullable=False, primary_key=True)
    pull_request_id = Column("pull_request_id", Integer(), ForeignKey('pull_requests.pull_request_id'), nullable=False)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=True)

    user = relationship('User')
    pull_request = relationship('PullRequest')


class Notification(Base, BaseModel):
    __tablename__ = 'notifications'
    __table_args__ = (
        Index('notification_type_idx', 'type'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )

    TYPE_CHANGESET_COMMENT = u'cs_comment'
    TYPE_MESSAGE = u'message'
    TYPE_MENTION = u'mention'
    TYPE_REGISTRATION = u'registration'
    TYPE_PULL_REQUEST = u'pull_request'
    TYPE_PULL_REQUEST_COMMENT = u'pull_request_comment'

    notification_id = Column('notification_id', Integer(), nullable=False, primary_key=True)
    subject = Column('subject', Unicode(512), nullable=True)
    body = Column('body', UnicodeText(50000), nullable=True)
    created_by = Column("created_by", Integer(), ForeignKey('users.user_id'), nullable=True)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    type_ = Column('type', Unicode(256))

    created_by_user = relationship('User')
    notifications_to_users = relationship('UserNotification', lazy='joined',
                                          cascade="all, delete, delete-orphan")

    @property
    def recipients(self):
        return [x.user for x in UserNotification.query()\
                .filter(UserNotification.notification == self)\
                .order_by(UserNotification.user_id.asc()).all()]

    @classmethod
    def create(cls, created_by, subject, body, recipients, type_=None):
        if type_ is None:
            type_ = Notification.TYPE_MESSAGE

        notification = cls()
        notification.created_by_user = created_by
        notification.subject = subject
        notification.body = body
        notification.type_ = type_
        notification.created_on = datetime.datetime.now()

        for u in recipients:
            assoc = UserNotification()
            assoc.notification = notification
            u.notifications.append(assoc)
        Session().add(notification)
        return notification

    @property
    def description(self):
        from rhodecode.model.notification import NotificationModel
        return NotificationModel().make_description(self)


class UserNotification(Base, BaseModel):
    __tablename__ = 'user_to_notification'
    __table_args__ = (
        UniqueConstraint('user_id', 'notification_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    user_id = Column('user_id', Integer(), ForeignKey('users.user_id'), primary_key=True)
    notification_id = Column("notification_id", Integer(), ForeignKey('notifications.notification_id'), primary_key=True)
    read = Column('read', Boolean, default=False)
    sent_on = Column('sent_on', DateTime(timezone=False), nullable=True, unique=None)

    user = relationship('User', lazy="joined")
    notification = relationship('Notification', lazy="joined",
                                order_by=lambda: Notification.created_on.desc(),)

    def mark_as_read(self):
        self.read = True
        Session().add(self)


class DbMigrateVersion(Base, BaseModel):
    __tablename__ = 'db_migrate_version'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    repository_id = Column('repository_id', String(250), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)
