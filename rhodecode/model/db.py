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
import time
import logging
import datetime
import traceback
import hashlib
import collections

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
from rhodecode.lib.vcs.backends.base import EmptyChangeset

from rhodecode.lib.utils2 import str2bool, safe_str, get_changeset_safe, \
    safe_unicode, remove_suffix, remove_prefix, time_to_datetime, _set_extras
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
        # deprecated and left for backward compatibility
        return cls.get_all()

    @classmethod
    def get_all(cls):
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
        if self.app_settings_name in ["ldap_active",
                                      "default_repo_enable_statistics",
                                      "default_repo_enable_locking",
                                      "default_repo_private",
                                      "default_repo_enable_downloads"]:
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

    @classmethod
    def get_default_repo_settings(cls, cache=False, strip_prefix=False):
        ret = cls.query()\
                .filter(cls.app_settings_name.startswith('default_')).all()
        fd = {}
        for row in ret:
            key = row.app_settings_name
            if strip_prefix:
                key = remove_prefix(key, prefix='default_')
            fd.update({key: row.app_settings_value})

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

    # def __init__(self, section='', key='', value=''):
    #     self.ui_section = section
    #     self.ui_key = key
    #     self.ui_value = value

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

    user_log = relationship('UserLog')
    user_perms = relationship('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all')

    repositories = relationship('Repository')
    user_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')
    followings = relationship('UserFollowing', primaryjoin='UserFollowing.user_id==User.user_id', cascade='all')

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
    def ip_addresses(self):
        ret = UserIpMap.query().filter(UserIpMap.user == self).all()
        return [x.ip_addr for x in ret]

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

    @property
    def AuthUser(self):
        """
        Returns instance of AuthUser for this user
        """
        from rhodecode.lib.auth import AuthUser
        return AuthUser(user_id=self.user_id, api_key=self.api_key,
                        username=self.username)

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

    @classmethod
    def get_from_cs_author(cls, author):
        """
        Tries to get User objects out of commit author string

        :param author:
        """
        from rhodecode.lib.helpers import email, author_name
        # Valid email in the attribute passed, see if they're in the system
        _email = email(author)
        if _email:
            user = cls.get_by_email(_email, case_insensitive=True)
            if user:
                return user
        # Maybe we can match by username?
        _author = author_name(author)
        user = cls.get_by_username(_author, case_insensitive=True)
        if user:
            return user

    def update_lastlogin(self):
        """Update user lastlogin"""
        self.last_login = datetime.datetime.now()
        Session().add(self)
        log.debug('updated user %s lastlogin' % self.username)

    @classmethod
    def get_first_admin(cls):
        user = User.query().filter(User.admin == True).first()
        if user is None:
            raise Exception('Missing administrative account!')
        return user

    @classmethod
    def get_default_user(cls, cache=False):
        user = User.get_by_username(User.DEFAULT_USER, cache=cache)
        if user is None:
            raise Exception('Missing default account!')
        return user

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
            ip_addresses=user.ip_addresses
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


class UserIpMap(Base, BaseModel):
    __tablename__ = 'user_ip_map'
    __table_args__ = (
        UniqueConstraint('user_id', 'ip_addr'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    __mapper_args__ = {}

    ip_id = Column("ip_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    ip_addr = Column("ip_addr", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=False, default=None)
    active = Column("active", Boolean(), nullable=True, unique=None, default=True)
    user = relationship('User', lazy='joined')

    @classmethod
    def _get_ip_range(cls, ip_addr):
        from rhodecode.lib import ipaddr
        net = ipaddr.IPNetwork(address=ip_addr)
        return [str(net.network), str(net.broadcast)]

    def __json__(self):
        return dict(
          ip_addr=self.ip_addr,
          ip_range=self._get_ip_range(self.ip_addr)
        )


class UserLog(Base, BaseModel):
    __tablename__ = 'user_logs'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    user_log_id = Column("user_log_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)
    username = Column("username", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True)
    repository_name = Column("repository_name", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    user_ip = Column("user_ip", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", UnicodeText(1200000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DateTime(timezone=False), nullable=True, unique=None, default=None)

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (self.__class__.__name__,
                                      self.repository_name,
                                      self.action)

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
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)

    members = relationship('UserGroupMember', cascade="all, delete, delete-orphan", lazy="joined")
    users_group_to_perm = relationship('UserGroupToPerm', cascade='all')
    users_group_repo_to_perm = relationship('UserGroupRepoToPerm', cascade='all')
    users_group_repo_group_to_perm = relationship('UserGroupRepoGroupToPerm', cascade='all')
    user_user_group_to_perm = relationship('UserUserGroupToPerm ', cascade='all')
    user_group_user_group_to_perm = relationship('UserGroupUserGroupToPerm ', primaryjoin="UserGroupUserGroupToPerm.target_user_group_id==UserGroup.users_group_id", cascade='all')

    user = relationship('User')

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (self.__class__.__name__,
                                      self.users_group_id,
                                      self.users_group_name)

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


class RepositoryField(Base, BaseModel):
    __tablename__ = 'repositories_fields'
    __table_args__ = (
        UniqueConstraint('repository_id', 'field_key'),  # no-multi field
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    PREFIX = 'ex_'  # prefix used in form to not conflict with already existing fields

    repo_field_id = Column("repo_field_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)
    field_key = Column("field_key", String(250, convert_unicode=False, assert_unicode=None))
    field_label = Column("field_label", String(1024, convert_unicode=False, assert_unicode=None), nullable=False)
    field_value = Column("field_value", String(10000, convert_unicode=False, assert_unicode=None), nullable=False)
    field_desc = Column("field_desc", String(1024, convert_unicode=False, assert_unicode=None), nullable=False)
    field_type = Column("field_type", String(256), nullable=False, unique=None)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)

    repository = relationship('Repository')

    @property
    def field_key_prefixed(self):
        return 'ex_%s' % self.field_key

    @classmethod
    def un_prefix_key(cls, key):
        if key.startswith(cls.PREFIX):
            return key[len(cls.PREFIX):]
        return key

    @classmethod
    def get_by_key_name(cls, key, repo):
        row = cls.query()\
                .filter(cls.repository == repo)\
                .filter(cls.field_key == key).scalar()
        return row


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
    _changeset_cache = Column("changeset_cache", LargeBinary(), nullable=True) #JSON data

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
    extra_fields = relationship('RepositoryField',
                                cascade="all, delete, delete-orphan")

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

    @hybrid_property
    def changeset_cache(self):
        from rhodecode.lib.vcs.backends.base import EmptyChangeset
        dummy = EmptyChangeset().__json__()
        if not self._changeset_cache:
            return dummy
        try:
            return json.loads(self._changeset_cache)
        except TypeError:
            return dummy

    @changeset_cache.setter
    def changeset_cache(self, val):
        try:
            self._changeset_cache = json.dumps(val)
        except Exception:
            log.error(traceback.format_exc())

    @classmethod
    def url_sep(cls):
        return URL_SEP

    @classmethod
    def normalize_repo_name(cls, repo_name):
        """
        Normalizes os specific repo_name to the format internally stored inside
        dabatabase using URL_SEP

        :param cls:
        :param repo_name:
        """
        return cls.url_sep().join(repo_name.split(os.sep))

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
        repo_name = cls.normalize_repo_name(repo_name)
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
        return self.groups_with_parents, self.just_name, self.repo_name

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
        return os.path.join(*map(safe_unicode, p))

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
            fork_of=repo.fork.repo_name if repo.fork else None,
            enable_statistics=repo.enable_statistics,
            enable_locking=repo.enable_locking,
            enable_downloads=repo.enable_downloads,
            last_changeset=repo.changeset_cache,
            locked_by=User.get(self.locked[0]).get_api_data() \
                if self.locked[0] else None,
            locked_date=time_to_datetime(self.locked[1]) \
                if self.locked[1] else None
        )
        rc_config = RhodeCodeSetting.get_app_settings()
        repository_fields = str2bool(rc_config.get('rhodecode_repository_fields'))
        if repository_fields:
            for f in self.extra_fields:
                data[f.field_key_prefixed] = f.field_value

        return data

    @classmethod
    def lock(cls, repo, user_id, lock_time=None):
        if not lock_time:
            lock_time = time.time()
        repo.locked = [user_id, lock_time]
        Session().add(repo)
        Session().commit()

    @classmethod
    def unlock(cls, repo):
        repo.locked = None
        Session().add(repo)
        Session().commit()

    @classmethod
    def getlock(cls, repo):
        return repo.locked

    @property
    def last_db_change(self):
        return self.updated_on

    def clone_url(self, **override):
        from pylons import url
        from urlparse import urlparse
        import urllib
        parsed_url = urlparse(url('home', qualified=True))
        default_clone_uri = '%(scheme)s://%(user)s%(pass)s%(netloc)s%(prefix)s%(path)s'
        decoded_path = safe_unicode(urllib.unquote(parsed_url.path))
        args = {
           'user': '',
           'pass': '',
           'scheme': parsed_url.scheme,
           'netloc': parsed_url.netloc,
           'prefix': decoded_path,
           'path': self.repo_name
        }

        args.update(override)
        return default_clone_uri % args

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

    def update_changeset_cache(self, cs_cache=None):
        """
        Update cache of last changeset for repository, keys should be::

            short_id
            raw_id
            revision
            message
            date
            author

        :param cs_cache:
        """
        from rhodecode.lib.vcs.backends.base import BaseChangeset
        if cs_cache is None:
            cs_cache = EmptyChangeset()
            # use no-cache version here
            scm_repo = self.scm_instance_no_cache()
            if scm_repo:
                cs_cache = scm_repo.get_changeset()

        if isinstance(cs_cache, BaseChangeset):
            cs_cache = cs_cache.__json__()

        if (cs_cache != self.changeset_cache or not self.changeset_cache):
            _default = datetime.datetime.fromtimestamp(0)
            last_change = cs_cache.get('date') or _default
            log.debug('updated repo %s with new cs cache %s'
                      % (self.repo_name, cs_cache))
            self.updated_on = last_change
            self.changeset_cache = cs_cache
            Session().add(self)
            Session().commit()
        else:
            log.debug('Skipping repo:%s already with latest changes'
                      % self.repo_name)

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
        grouped = collections.defaultdict(list)
        for cmt in cmts.all():
            grouped[cmt.revision].append(cmt)
        return grouped

    def statuses(self, revisions=None):
        """
        Returns statuses for this repository

        :param revisions: list of revisions to get statuses for
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

    def _repo_size(self):
        from rhodecode.lib import helpers as h
        log.debug('calculating repository size...')
        return h.format_byte_size(self.scm_instance.size)

    #==========================================================================
    # SCM CACHE INSTANCE
    #==========================================================================

    def set_invalidate(self):
        """
        Mark caches of this repo as invalid.
        """
        CacheInvalidation.set_invalidate(self.repo_name)

    def scm_instance_no_cache(self):
        return self.__get_instance()

    @property
    def scm_instance(self):
        import rhodecode
        full_cache = str2bool(rhodecode.CONFIG.get('vcs_full_cache'))
        if full_cache:
            return self.scm_instance_cached()
        return self.__get_instance()

    def scm_instance_cached(self, valid_cache_keys=None):
        @cache_region('long_term')
        def _c(repo_name):
            return self.__get_instance()
        rn = self.repo_name

        valid = CacheInvalidation.test_and_set_valid(rn, None, valid_cache_keys=valid_cache_keys)
        if not valid:
            log.debug('Cache for %s invalidated, getting new object' % (rn))
            region_invalidate(_c, None, rn)
        else:
            log.debug('Getting obj for %s from cache' % (rn))
        return _c(rn)

    def __get_instance(self):
        repo_full_path = self.repo_full_path
        try:
            alias = get_scm(repo_full_path)[0]
            log.debug('Creating instance of %s repository from %s'
                      % (alias, repo_full_path))
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
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)

    repo_group_to_perm = relationship('UserRepoGroupToPerm', cascade='all', order_by='UserRepoGroupToPerm.group_to_perm_id')
    users_group_to_perm = relationship('UserGroupRepoGroupToPerm', cascade='all')
    parent_group = relationship('RepoGroup', remote_side=group_id)
    user = relationship('User')

    def __init__(self, group_name='', parent_group=None):
        self.group_name = group_name
        self.parent_group = parent_group

    def __unicode__(self):
        return u"<%s('id:%s:%s')>" % (self.__class__.__name__, self.group_id,
                                      self.group_name)

    @classmethod
    def groups_choices(cls, groups=None, show_empty_group=True):
        from webhelpers.html import literal as _literal
        if not groups:
            groups = cls.query().all()

        repo_groups = []
        if show_empty_group:
            repo_groups = [('-1', u'-- %s --' % _('top level'))]
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

    def _recursive_objects(self, include_repos=True):
        all_ = []

        def _get_members(root_gr):
            if include_repos:
                for r in root_gr.repositories:
                    all_.append(r)
            childs = root_gr.children.all()
            if childs:
                for gr in childs:
                    all_.append(gr)
                    _get_members(gr)

        _get_members(self)
        return [self] + all_

    def recursive_groups_and_repos(self):
        """
        Recursive return all groups, with repositories in those groups
        """
        return self._recursive_objects()

    def recursive_groups(self):
        """
        Returns all children groups for this group including children of children
        """
        return self._recursive_objects(include_repos=False)

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
        ('hg.admin', _('RhodeCode Administrator')),

        ('repository.none', _('Repository no access')),
        ('repository.read', _('Repository read access')),
        ('repository.write', _('Repository write access')),
        ('repository.admin', _('Repository admin access')),

        ('group.none', _('Repository group no access')),
        ('group.read', _('Repository group read access')),
        ('group.write', _('Repository group write access')),
        ('group.admin', _('Repository group admin access')),

        ('usergroup.none', _('User group no access')),
        ('usergroup.read', _('User group read access')),
        ('usergroup.write', _('User group write access')),
        ('usergroup.admin', _('User group admin access')),

        ('hg.repogroup.create.false', _('Repository Group creation disabled')),
        ('hg.repogroup.create.true', _('Repository Group creation enabled')),

        ('hg.usergroup.create.false', _('User Group creation disabled')),
        ('hg.usergroup.create.true', _('User Group creation enabled')),

        ('hg.create.none', _('Repository creation disabled')),
        ('hg.create.repository', _('Repository creation enabled')),

        ('hg.fork.none', _('Repository forking disabled')),
        ('hg.fork.repository', _('Repository forking enabled')),

        ('hg.register.none', _('Registration disabled')),
        ('hg.register.manual_activate', _('User Registration with manual account activation')),
        ('hg.register.auto_activate', _('User Registration with automatic account activation')),

        ('hg.extern_activate.manual', _('Manual activation of external account')),
        ('hg.extern_activate.auto', _('Automatic activation of external account')),

    ]

    #definition of system default permissions for DEFAULT user
    DEFAULT_USER_PERMISSIONS = [
        'repository.read',
        'group.read',
        'usergroup.read',
        'hg.create.repository',
        'hg.fork.repository',
        'hg.register.manual_activate',
        'hg.extern_activate.auto',
    ]

    # defines which permissions are more important higher the more important
    # Weight defines which permissions are more important.
    # The higher number the more important.
    PERM_WEIGHTS = {
        'repository.none': 0,
        'repository.read': 1,
        'repository.write': 3,
        'repository.admin': 4,

        'group.none': 0,
        'group.read': 1,
        'group.write': 3,
        'group.admin': 4,

        'usergroup.none': 0,
        'usergroup.read': 1,
        'usergroup.write': 3,
        'usergroup.admin': 4,
        'hg.repogroup.create.false': 0,
        'hg.repogroup.create.true': 1,

        'hg.usergroup.create.false': 0,
        'hg.usergroup.create.true': 1,

        'hg.fork.none': 0,
        'hg.fork.repository': 1,
        'hg.create.none': 0,
        'hg.create.repository': 1
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

    @classmethod
    def get_default_user_group_perms(cls, default_user_id):
        q = Session().query(UserUserGroupToPerm, UserGroup, cls)\
         .join((UserGroup, UserUserGroupToPerm.user_group_id == UserGroup.users_group_id))\
         .join((cls, UserUserGroupToPerm.permission_id == cls.permission_id))\
         .filter(UserUserGroupToPerm.user_id == default_user_id)

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
        return u'<%s => %s >' % (self.user, self.repository)


class UserUserGroupToPerm(Base, BaseModel):
    __tablename__ = 'user_user_group_to_perm'
    __table_args__ = (
        UniqueConstraint('user_id', 'user_group_id', 'permission_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    user_user_group_to_perm_id = Column("user_user_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    user_group_id = Column("user_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    user_group = relationship('UserGroup')
    permission = relationship('Permission')

    @classmethod
    def create(cls, user, user_group, permission):
        n = cls()
        n.user = user
        n.user_group = user_group
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<%s => %s >' % (self.user, self.user_group)


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

    def __unicode__(self):
        return u'<%s => %s >' % (self.user, self.permission)


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
        return u'<UserGroupRepoToPerm:%s => %s >' % (self.users_group, self.repository)


class UserGroupUserGroupToPerm(Base, BaseModel):
    __tablename__ = 'user_group_user_group_to_perm'
    __table_args__ = (
        UniqueConstraint('target_user_group_id', 'user_group_id', 'permission_id'),
        CheckConstraint('target_user_group_id != user_group_id'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'}
    )
    user_group_user_group_to_perm_id = Column("user_group_user_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    target_user_group_id = Column("target_user_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    user_group_id = Column("user_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)

    target_user_group = relationship('UserGroup', primaryjoin='UserGroupUserGroupToPerm.target_user_group_id==UserGroup.users_group_id')
    user_group = relationship('UserGroup', primaryjoin='UserGroupUserGroupToPerm.user_group_id==UserGroup.users_group_id')
    permission = relationship('Permission')

    @classmethod
    def create(cls, target_user_group, user_group, permission):
        n = cls()
        n.target_user_group = target_user_group
        n.user_group = user_group
        n.permission = permission
        Session().add(n)
        return n

    def __unicode__(self):
        return u'<UserGroupUserGroup:%s => %s >' % (self.target_user_group, self.user_group)


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
    # cache_id, not used
    cache_id = Column("cache_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    # cache_key as created by _get_cache_key
    cache_key = Column("cache_key", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    # cache_args is a repo_name
    cache_args = Column("cache_args", String(255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    # instance sets cache_active True when it is caching,
    # other instances set cache_active to False to indicate that this cache is invalid
    cache_active = Column("cache_active", Boolean(), nullable=True, unique=None, default=False)

    def __init__(self, cache_key, repo_name=''):
        self.cache_key = cache_key
        self.cache_args = repo_name
        self.cache_active = False

    def __unicode__(self):
        return u"<%s('%s:%s[%s]')>" % (self.__class__.__name__,
                            self.cache_id, self.cache_key, self.cache_active)

    def _cache_key_partition(self):
        prefix, repo_name, suffix = self.cache_key.partition(self.cache_args)
        return prefix, repo_name, suffix

    def get_prefix(self):
        """
        get prefix that might have been used in _get_cache_key to
        generate self.cache_key. Only used for informational purposes
        in repo_edit.html.
        """
        # prefix, repo_name, suffix
        return self._cache_key_partition()[0]

    def get_suffix(self):
        """
        get suffix that might have been used in _get_cache_key to
        generate self.cache_key. Only used for informational purposes
        in repo_edit.html.
        """
        # prefix, repo_name, suffix
        return self._cache_key_partition()[2]

    @classmethod
    def clear_cache(cls):
        """
        Delete all cache keys from database.
        Should only be run when all instances are down and all entries thus stale.
        """
        cls.query().delete()
        Session().commit()

    @classmethod
    def _get_cache_key(cls, key):
        """
        Wrapper for generating a unique cache key for this instance and "key".
        key must / will start with a repo_name which will be stored in .cache_args .
        """
        import rhodecode
        prefix = rhodecode.CONFIG.get('instance_id', '')
        return "%s%s" % (prefix, key)

    @classmethod
    def set_invalidate(cls, repo_name):
        """
        Mark all caches of a repo as invalid in the database.
        """
        inv_objs = Session().query(cls).filter(cls.cache_args == repo_name).all()

        try:
            for inv_obj in inv_objs:
                log.debug('marking %s key for invalidation based on repo_name=%s'
                          % (inv_obj, safe_str(repo_name)))
                inv_obj.cache_active = False
                Session().add(inv_obj)
            Session().commit()
        except Exception:
            log.error(traceback.format_exc())
            Session().rollback()

    @classmethod
    def test_and_set_valid(cls, repo_name, kind, valid_cache_keys=None):
        """
        Mark this cache key as active and currently cached.
        Return True if the existing cache registration still was valid.
        Return False to indicate that it had been invalidated and caches should be refreshed.
        """

        key = (repo_name + '_' + kind) if kind else repo_name
        cache_key = cls._get_cache_key(key)

        if valid_cache_keys and cache_key in valid_cache_keys:
            return True

        try:
            inv_obj = cls.query().filter(cls.cache_key == cache_key).scalar()
            if not inv_obj:
                inv_obj = CacheInvalidation(cache_key, repo_name)
            was_valid = inv_obj.cache_active
            inv_obj.cache_active = True
            Session().add(inv_obj)
            Session().commit()
            return was_valid
        except Exception:
            log.error(traceback.format_exc())
            Session().rollback()
            return False

    @classmethod
    def get_valid_cache_keys(cls):
        """
        Return opaque object with information of which caches still are valid
        and can be used without checking for invalidation.
        """
        return set(inv_obj.cache_key for inv_obj in cls.query().filter(cls.cache_active).all())


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

    # values for .status
    STATUS_NEW = u'new'
    STATUS_OPEN = u'open'
    STATUS_CLOSED = u'closed'

    pull_request_id = Column('pull_request_id', Integer(), nullable=False, primary_key=True)
    title = Column('title', Unicode(256), nullable=True)
    description = Column('description', UnicodeText(10240), nullable=True)
    status = Column('status', Unicode(256), nullable=False, default=STATUS_NEW) # only for closedness, not approve/reject/etc
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

    @property
    def org_ref_parts(self):
        return self.org_ref.split(':')

    @property
    def other_ref_parts(self):
        return self.other_ref.split(':')

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

    @property
    def last_review_status(self):
        return self.statuses[-1].status if self.statuses else ''

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


class Gist(Base, BaseModel):
    __tablename__ = 'gists'
    __table_args__ = (
        Index('g_gist_access_id_idx', 'gist_access_id'),
        Index('g_created_on_idx', 'created_on'),
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8', 'sqlite_autoincrement': True}
    )
    GIST_PUBLIC = u'public'
    GIST_PRIVATE = u'private'

    gist_id = Column('gist_id', Integer(), primary_key=True)
    gist_access_id = Column('gist_access_id', Unicode(250))
    gist_description = Column('gist_description', UnicodeText(1024))
    gist_owner = Column('user_id', Integer(), ForeignKey('users.user_id'), nullable=True)
    gist_expires = Column('gist_expires', Float(53), nullable=False)
    gist_type = Column('gist_type', Unicode(128), nullable=False)
    created_on = Column('created_on', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)
    modified_at = Column('modified_at', DateTime(timezone=False), nullable=False, default=datetime.datetime.now)

    owner = relationship('User')

    @classmethod
    def get_or_404(cls, id_):
        res = cls.query().filter(cls.gist_access_id == id_).scalar()
        if not res:
            raise HTTPNotFound
        return res

    @classmethod
    def get_by_access_id(cls, gist_access_id):
        return cls.query().filter(cls.gist_access_id == gist_access_id).scalar()

    def gist_url(self):
        import rhodecode
        alias_url = rhodecode.CONFIG.get('gist_alias_url')
        if alias_url:
            return alias_url.replace('{gistid}', self.gist_access_id)

        from pylons import url
        return url('gist', gist_id=self.gist_access_id, qualified=True)

    @classmethod
    def base_path(cls):
        """
        Returns base path when all gists are stored

        :param cls:
        """
        from rhodecode.model.gist import GIST_STORE_LOC
        q = Session().query(RhodeCodeUi)\
            .filter(RhodeCodeUi.ui_key == URL_SEP)
        q = q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return os.path.join(q.one().ui_value, GIST_STORE_LOC)

    def get_api_data(self):
        """
        Common function for generating gist related data for API
        """
        gist = self
        data = dict(
            gist_id=gist.gist_id,
            type=gist.gist_type,
            access_id=gist.gist_access_id,
            description=gist.gist_description,
            url=gist.gist_url(),
            expires=gist.gist_expires,
            created_on=gist.created_on,
        )
        return data

    def __json__(self):
        data = dict(
        )
        data.update(self.get_api_data())
        return data
    ## SCM functions

    @property
    def scm_instance(self):
        from rhodecode.lib.vcs import get_repo
        base_path = self.base_path()
        return get_repo(os.path.join(*map(safe_str,
                                          [base_path, self.gist_access_id])))


class DbMigrateVersion(Base, BaseModel):
    __tablename__ = 'db_migrate_version'
    __table_args__ = (
        {'extend_existing': True, 'mysql_engine': 'InnoDB',
         'mysql_charset': 'utf8'},
    )
    repository_id = Column('repository_id', String(250), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)
