# -*- coding: utf-8 -*-
"""
    rhodecode.model.db
    ~~~~~~~~~~~~~~~~~~
    
    Database Models for RhodeCode
    
    :created_on: Apr 08, 2010
    :author: marcink
    :copyright: (C) 2009-2011 Marcin Kuzminski <marcin@python-works.com>    
    :license: GPLv3, see COPYING for more details.
"""
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
import logging
import datetime
from datetime import date

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relationship, backref, class_mapper
from sqlalchemy.orm.session import Session

from rhodecode.model.meta import Base

log = logging.getLogger(__name__)

class BaseModel(object):

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

class RhodeCodeSettings(Base, BaseModel):
    __tablename__ = 'rhodecode_settings'
    __table_args__ = (UniqueConstraint('app_settings_name'), {'useexisting':True})
    app_settings_id = Column("app_settings_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    app_settings_name = Column("app_settings_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    app_settings_value = Column("app_settings_value", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __init__(self, k='', v=''):
        self.app_settings_name = k
        self.app_settings_value = v

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.app_settings_name, self.app_settings_value)

class RhodeCodeUi(Base, BaseModel):
    __tablename__ = 'rhodecode_ui'
    __table_args__ = {'useexisting':True}
    ui_id = Column("ui_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    ui_section = Column("ui_section", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_key = Column("ui_key", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_value = Column("ui_value", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_active = Column("ui_active", Boolean(), nullable=True, unique=None, default=True)


class User(Base, BaseModel):
    __tablename__ = 'users'
    __table_args__ = (UniqueConstraint('username'), UniqueConstraint('email'), {'useexisting':True})
    user_id = Column("user_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    username = Column("username", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", Boolean(), nullable=True, unique=None, default=None)
    admin = Column("admin", Boolean(), nullable=True, unique=None, default=False)
    name = Column("name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    lastname = Column("lastname", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    email = Column("email", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    last_login = Column("last_login", DateTime(timezone=False), nullable=True, unique=None, default=None)
    ldap_dn = Column("ldap_dn", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    user_log = relationship('UserLog', cascade='all')
    user_perms = relationship('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all')

    repositories = relationship('Repository')
    user_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')

    @property
    def full_contact(self):
        return '%s %s <%s>' % (self.name, self.lastname, self.email)


    @property
    def is_admin(self):
        return self.admin

    def __repr__(self):
        return "<%s('id:%s:%s')>" % (self.__class__.__name__,
                                     self.user_id, self.username)

    def update_lastlogin(self):
        """Update user lastlogin"""

        try:
            session = Session.object_session(self)
            self.last_login = datetime.datetime.now()
            session.add(self)
            session.commit()
            log.debug('updated user %s lastlogin', self.username)
        except (DatabaseError,):
            session.rollback()


class UserLog(Base, BaseModel):
    __tablename__ = 'user_logs'
    __table_args__ = {'useexisting':True}
    user_log_id = Column("user_log_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(length=None, convert_unicode=False, assert_unicode=None), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)
    repository_name = Column("repository_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    user_ip = Column("user_ip", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DateTime(timezone=False), nullable=True, unique=None, default=None)

    @property
    def action_as_day(self):
        return date(*self.action_date.timetuple()[:3])

    user = relationship('User')
    repository = relationship('Repository')


class UsersGroup(Base, BaseModel):
    __tablename__ = 'users_groups'
    __table_args__ = {'useexisting':True}

    users_group_id = Column("users_group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_name = Column("users_group_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    users_group_active = Column("users_group_active", Boolean(), nullable=True, unique=None, default=None)

    members = relationship('UsersGroupMember', cascade="all, delete, delete-orphan", lazy="joined")

class UsersGroupMember(Base, BaseModel):
    __tablename__ = 'users_groups_members'
    __table_args__ = {'useexisting':True}

    users_group_member_id = Column("users_group_member_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)

    user = relationship('User', lazy='joined')
    users_group = relationship('UsersGroup')

    def __init__(self, gr_id, u_id):
        self.users_group_id = gr_id
        self.user_id = u_id

class Repository(Base, BaseModel):
    __tablename__ = 'repositories'
    __table_args__ = (UniqueConstraint('repo_name'), {'useexisting':True},)
    repo_id = Column("repo_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repo_name = Column("repo_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    repo_type = Column("repo_type", String(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=False, default='hg')
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", Boolean(), nullable=True, unique=None, default=None)
    enable_statistics = Column("statistics", Boolean(), nullable=True, unique=None, default=True)
    enable_downloads = Column("downloads", Boolean(), nullable=True, unique=None, default=True)
    description = Column("description", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    fork_id = Column("fork_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=False, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=False, default=None)

    user = relationship('User')
    fork = relationship('Repository', remote_side=repo_id)
    group = relationship('Group')
    repo_to_perm = relationship('RepoToPerm', cascade='all')
    users_group_to_perm = relationship('UsersGroupToPerm', cascade='all')
    stats = relationship('Statistics', cascade='all', uselist=False)

    repo_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_repo_id==Repository.repo_id', cascade='all')

    logs = relationship('UserLog', cascade='all')

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.repo_id, self.repo_name)

class Group(Base, BaseModel):
    __tablename__ = 'groups'
    __table_args__ = (UniqueConstraint('group_name'), {'useexisting':True},)

    group_id = Column("group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    group_name = Column("group_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    group_parent_id = Column("group_parent_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=None, default=None)

    parent_group = relationship('Group', remote_side=group_id)


    def __init__(self, group_name='', parent_group=None):
        self.group_name = group_name
        self.parent_group = parent_group

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__, self.group_id,
                                  self.group_name)

class Permission(Base, BaseModel):
    __tablename__ = 'permissions'
    __table_args__ = {'useexisting':True}
    permission_id = Column("permission_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.permission_id, self.permission_name)

class RepoToPerm(Base, BaseModel):
    __tablename__ = 'repo_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'repository_id'), {'useexisting':True})
    repo_to_perm_id = Column("repo_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')
    repository = relationship('Repository')

class UserToPerm(Base, BaseModel):
    __tablename__ = 'user_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'permission_id'), {'useexisting':True})
    user_to_perm_id = Column("user_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')


class UsersGroupToPerm(Base, BaseModel):
    __tablename__ = 'users_group_to_perm'
    __table_args__ = (UniqueConstraint('users_group_id', 'permission_id'), {'useexisting':True})
    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UsersGroup')
    permission = relationship('Permission')
    repository = relationship('Repository')

class GroupToPerm(Base, BaseModel):
    __tablename__ = 'group_to_perm'
    __table_args__ = (UniqueConstraint('group_id', 'permission_id'), {'useexisting':True})

    group_to_perm_id = Column("group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')
    group = relationship('Group')

class Statistics(Base, BaseModel):
    __tablename__ = 'statistics'
    __table_args__ = (UniqueConstraint('repository_id'), {'useexisting':True})
    stat_id = Column("stat_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=True, default=None)
    stat_on_revision = Column("stat_on_revision", Integer(), nullable=False)
    commit_activity = Column("commit_activity", LargeBinary(), nullable=False)#JSON data
    commit_activity_combined = Column("commit_activity_combined", LargeBinary(), nullable=False)#JSON data
    languages = Column("languages", LargeBinary(), nullable=False)#JSON data

    repository = relationship('Repository', single_parent=True)

class UserFollowing(Base, BaseModel):
    __tablename__ = 'user_followings'
    __table_args__ = (UniqueConstraint('user_id', 'follows_repository_id'),
                      UniqueConstraint('user_id', 'follows_user_id')
                      , {'useexisting':True})

    user_following_id = Column("user_following_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    follows_repo_id = Column("follows_repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=None, default=None)
    follows_user_id = Column("follows_user_id", Integer(), ForeignKey('users.user_id'), nullable=True, unique=None, default=None)

    user = relationship('User', primaryjoin='User.user_id==UserFollowing.user_id')

    follows_user = relationship('User', primaryjoin='User.user_id==UserFollowing.follows_user_id')
    follows_repository = relationship('Repository', order_by='Repository.repo_name')

class CacheInvalidation(Base, BaseModel):
    __tablename__ = 'cache_invalidation'
    __table_args__ = (UniqueConstraint('cache_key'), {'useexisting':True})
    cache_id = Column("cache_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    cache_key = Column("cache_key", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_args = Column("cache_args", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    cache_active = Column("cache_active", Boolean(), nullable=True, unique=None, default=False)


    def __init__(self, cache_key, cache_args=''):
        self.cache_key = cache_key
        self.cache_args = cache_args
        self.cache_active = False

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.cache_id, self.cache_key)

class DbMigrateVersion(Base, BaseModel):
    __tablename__ = 'db_migrate_version'
    __table_args__ = {'useexisting':True}
    repository_id = Column('repository_id', String(250), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)

