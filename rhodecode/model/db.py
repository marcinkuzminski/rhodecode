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
from datetime import date

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.interfaces import MapperExtension

from rhodecode.lib import str2bool
from rhodecode.model.meta import Base, Session
from rhodecode.model.caching_query import FromCache

log = logging.getLogger(__name__)

#==============================================================================
# MAPPER EXTENSIONS
#==============================================================================

class RepositoryMapper(MapperExtension):
    def after_update(self, mapper, connection, instance):
        pass


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


    @classmethod
    def get_by_name(cls, ldap_key):
        return Session.query(cls)\
            .filter(cls.app_settings_name == ldap_key).scalar()

    @classmethod
    def get_app_settings(cls, cache=False):

        ret = Session.query(cls)

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
        ret = Session.query(cls)\
                .filter(cls.app_settings_name.startswith('ldap_'))\
                .all()
        fd = {}
        for row in ret:
            fd.update({row.app_settings_name:row.app_settings_value})
        return fd


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
    ldap_dn = Column("ldap_dn", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    api_key = Column("api_key", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    user_log = relationship('UserLog', cascade='all')
    user_perms = relationship('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all')

    repositories = relationship('Repository')
    user_followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')

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


class UsersGroup(Base):
    __tablename__ = 'users_groups'
    __table_args__ = {'useexisting':True}

    users_group_id = Column("users_group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_name = Column("users_group_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    users_group_active = Column("users_group_active", Boolean(), nullable=True, unique=None, default=None)

    members = relationship('UsersGroupMember', cascade="all, delete, delete-orphan", lazy="joined")


    @classmethod
    def get_by_group_name(cls, group_name, cache=False, case_insensitive=False):
        if case_insensitive:
            gr = Session.query(cls)\
            .filter(cls.users_group_name.ilike(group_name))
        else:
            gr = Session.query(UsersGroup)\
                .filter(UsersGroup.users_group_name == group_name)
        if cache:
            gr = gr.options(FromCache("sql_cache_short",
                                          "get_user_%s" % group_name))
        return gr.scalar()

class UsersGroupMember(Base):
    __tablename__ = 'users_groups_members'
    __table_args__ = {'useexisting':True}

    users_group_member_id = Column("users_group_member_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)

    user = relationship('User', lazy='joined')
    users_group = relationship('UsersGroup')

    def __init__(self, gr_id='', u_id=''):
        self.users_group_id = gr_id
        self.user_id = u_id

class Repository(Base):
    __tablename__ = 'repositories'
    __table_args__ = (UniqueConstraint('repo_name'), {'useexisting':True},)
    __mapper_args__ = {'extension':RepositoryMapper()}

    repo_id = Column("repo_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repo_name = Column("repo_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    clone_uri = Column("clone_uri", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=False, default=None)
    repo_type = Column("repo_type", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=False, default='hg')
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", Boolean(), nullable=True, unique=None, default=None)
    enable_statistics = Column("statistics", Boolean(), nullable=True, unique=None, default=True)
    enable_downloads = Column("downloads", Boolean(), nullable=True, unique=None, default=True)
    description = Column("description", String(length=10000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    fork_id = Column("fork_id", Integer(), ForeignKey('repositories.repo_id'), nullable=True, unique=False, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=False, default=None)


    user = relationship('User')
    fork = relationship('Repository', remote_side=repo_id)
    group = relationship('Group')
    repo_to_perm = relationship('RepoToPerm', cascade='all', order_by='RepoToPerm.repo_to_perm_id')
    users_group_to_perm = relationship('UsersGroupRepoToPerm', cascade='all')
    stats = relationship('Statistics', cascade='all', uselist=False)

    followers = relationship('UserFollowing', primaryjoin='UserFollowing.follows_repo_id==Repository.repo_id', cascade='all')

    logs = relationship('UserLog', cascade='all')

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.repo_id, self.repo_name)

    @classmethod
    def by_repo_name(cls, repo_name):
        return Session.query(cls).filter(cls.repo_name == repo_name).one()

    @property
    def just_name(self):
        return self.repo_name.split(os.sep)[-1]

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


class Group(Base):
    __tablename__ = 'groups'
    __table_args__ = (UniqueConstraint('group_name'), {'useexisting':True},)

    group_id = Column("group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    group_name = Column("group_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    group_parent_id = Column("group_parent_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=None, default=None)

    parent_group = relationship('Group', remote_side=group_id)


    def __init__(self, group_name='', parent_group=None):
        self.group_name = group_name
        self.parent_group = parent_group

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__, self.group_id,
                                  self.group_name)

    @property
    def parents(self):
        groups = []
        if self.parent_group is None:
            return groups
        cur_gr = self.parent_group
        groups.insert(0, cur_gr)
        while 1:
            gr = getattr(cur_gr, 'parent_group', None)
            cur_gr = cur_gr.parent_group
            if gr is None:
                break
            groups.insert(0, gr)
        return groups

    @property
    def repositories(self):
        return Session.query(Repository).filter(Repository.group == self).all()

class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = {'useexisting':True}
    permission_id = Column("permission_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__,
                                  self.permission_id, self.permission_name)

    @classmethod
    def get_by_key(cls, key):
        return Session.query(cls).filter(cls.permission_name == key).scalar()

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

    @classmethod
    def has_perm(cls, user_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        return Session.query(cls).filter(cls.user_id == user_id)\
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
            Session.query(cls).filter(cls.user_id == user_id)\
                .filter(cls.permission == perm).delete()
            Session.commit()
        except:
            Session.rollback()

class UsersGroupRepoToPerm(Base):
    __tablename__ = 'users_group_repo_to_perm'
    __table_args__ = (UniqueConstraint('users_group_id', 'permission_id'), {'useexisting':True})
    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey('repositories.repo_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UsersGroup')
    permission = relationship('Permission')
    repository = relationship('Repository')


class UsersGroupToPerm(Base):
    __tablename__ = 'users_group_to_perm'
    users_group_to_perm_id = Column("users_group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    users_group_id = Column("users_group_id", Integer(), ForeignKey('users_groups.users_group_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)

    users_group = relationship('UsersGroup')
    permission = relationship('Permission')


    @classmethod
    def has_perm(cls, users_group_id, perm):
        if not isinstance(perm, Permission):
            raise Exception('perm needs to be an instance of Permission class')

        return Session.query(cls).filter(cls.users_group_id ==
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
            Session.query(cls).filter(cls.users_group_id == users_group_id)\
                .filter(cls.permission == perm).delete()
            Session.commit()
        except:
            Session.rollback()


class GroupToPerm(Base):
    __tablename__ = 'group_to_perm'
    __table_args__ = (UniqueConstraint('group_id', 'permission_id'), {'useexisting':True})

    group_to_perm_id = Column("group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')
    group = relationship('Group')

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
    follows_from = Column('follows_from', DateTime(timezone=False), nullable=True, unique=None, default=datetime.datetime.now)

    user = relationship('User', primaryjoin='User.user_id==UserFollowing.user_id')

    follows_user = relationship('User', primaryjoin='User.user_id==UserFollowing.follows_user_id')
    follows_repository = relationship('Repository', order_by='Repository.repo_name')



    @classmethod
    def get_repo_followers(cls, repo_id):
        return Session.query(cls).filter(cls.follows_repo_id == repo_id)

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
    repository_id = Column('repository_id', String(250), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)
