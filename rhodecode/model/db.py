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
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.interfaces import MapperExtension

from rhodecode.model.meta import Base, Session

log = logging.getLogger(__name__)


class RhodeCodeSettings(Base):
    __tablename__ = 'rhodecode_settings'
    __table_args__ = (UniqueConstraint('app_settings_name'), {'useexisting':True})
    app_settings_id = Column("app_settings_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    app_settings_name = Column("app_settings_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    app_settings_value = Column("app_settings_value", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __init__(self, k='', v=''):
        self.app_settings_name = k
        self.app_settings_value = v

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.app_settings_name, self.app_settings_value)

class RhodeCodeUi(Base):
    __tablename__ = 'rhodecode_ui'
    __table_args__ = {'useexisting':True}
    ui_id = Column("ui_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    ui_section = Column("ui_section", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_key = Column("ui_key", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_value = Column("ui_value", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_active = Column("ui_active", Boolean(), nullable=True, unique=None, default=True)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (UniqueConstraint('username'), UniqueConstraint('email'), {'useexisting':True})
    user_id = Column("user_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    username = Column("username", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    password = Column("password", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    active = Column("active", Boolean(), nullable=True, unique=None, default=None)
    admin = Column("admin", Boolean(), nullable=True, unique=None, default=False)
    name = Column("name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    lastname = Column("lastname", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    email = Column("email", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    last_login = Column("last_login", DateTime(timezone=False), nullable=True, unique=None, default=None)
    is_ldap = Column("is_ldap", Boolean(), nullable=False, unique=None, default=False)

    user_log = relationship('UserLog', cascade='all')
    user_perms = relationship('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all')

    repositories = relationship('Repository')
    user_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')

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
        return "<%s('id:%s:%s')>" % (self.__class__.__name__,
                                     self.user_id, self.username)

    @classmethod
    def by_username(cls, username):
        return Session.query(cls).filter(cls.username == username).one()


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


class UserLog(Base):
    __tablename__ = 'user_logs'
    __table_args__ = {'useexisting':True}
    user_log_id = Column("user_log_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(length=None, convert_unicode=False, assert_unicode=None), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)
    repository_name = Column("repository_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    user_ip = Column("user_ip", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", UnicodeText(length=1200000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DateTime(timezone=False), nullable=True, unique=None, default=None)

    @property
    def action_as_day(self):
        return date(*self.action_date.timetuple()[:3])

    user = relationship('User')
    repository = relationship('Repository')

class Repository(Base):
    __tablename__ = 'repositories'
    __table_args__ = (UniqueConstraint('repo_name'), {'useexisting':True},)
    repo_id = Column("repo_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repo_name = Column("repo_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    repo_type = Column("repo_type", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=False, default='hg')
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", Boolean(), nullable=True, unique=None, default=None)
    enable_statistics = Column("statistics", Boolean(), nullable=True, unique=None, default=True)
    description = Column("description", String(length=10000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    fork_id = Column("fork_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=False, default=None)

    user = relationship('User')
    fork = relationship('Repository', remote_side=repo_id)
    repo_to_perm = relationship('RepoToPerm', cascade='all')
    stats = relationship('Statistics', cascade='all', uselist=False)

    repo_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_repo_id==Repository.repo_id', cascade='all')

    logs = relationship('UserLog', cascade='all')

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.repo_id, self.repo_name)

class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = {'useexisting':True}
    permission_id = Column("permission_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.permission_id, self.permission_name)

class RepoToPerm(Base):
    __tablename__ = 'repo_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'repository_id'), {'useexisting':True})
    repo_to_perm_id = Column("repo_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')
    repository = relationship('Repository')

class UserToPerm(Base):
    __tablename__ = 'user_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'permission_id'), {'useexisting':True})
    user_to_perm_id = Column("user_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')

class Statistics(Base):
    __tablename__ = 'statistics'
    __table_args__ = (UniqueConstraint('repository_id'), {'useexisting':True})
    stat_id = Column("stat_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=True, default=None)
    stat_on_revision = Column("stat_on_revision", Integer(), nullable=False)
    commit_activity = Column("commit_activity", LargeBinary(1000000), nullable=False)#JSON data
    commit_activity_combined = Column("commit_activity_combined", LargeBinary(), nullable=False)#JSON data
    languages = Column("languages", LargeBinary(1000000), nullable=False)#JSON data

    repository = relationship('Repository', single_parent=True)

class UserFollowing(Base):
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

class CacheInvalidation(Base):
    __tablename__ = 'cache_invalidation'
    __table_args__ = (UniqueConstraint('cache_key'), {'useexisting':True})
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

class DbMigrateVersion(Base):
    __tablename__ = 'db_migrate_version'
    __table_args__ = {'useexisting':True}
    repository_id = Column('repository_id', String(255), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)

