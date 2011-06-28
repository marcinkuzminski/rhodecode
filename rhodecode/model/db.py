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
import traceback
from datetime import date

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relationship, backref, joinedload, class_mapper
from sqlalchemy.orm.interfaces import MapperExtension

from beaker.cache import cache_region, region_invalidate

from vcs import get_backend
from vcs.utils.helpers import get_scm
from vcs.exceptions import RepositoryError, VCSError
from vcs.utils.lazy import LazyProperty
from vcs.nodes import FileNode

from rhodecode.lib import str2bool, json
from rhodecode.model.meta import Base, Session
from rhodecode.model.caching_query import FromCache

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
        return Session.query(cls).get(id_)


class RhodeCodeSettings(Base, BaseModel):
    __tablename__ = 'rhodecode_settings'
    __table_args__ = (UniqueConstraint('app_settings_name'), {'extend_existing':True})
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

        fd.update({'ldap_active':str2bool(fd.get('ldap_active'))})

        return fd


class RhodeCodeUi(Base, BaseModel):
    __tablename__ = 'rhodecode_ui'
    __table_args__ = {'extend_existing':True}
    ui_id = Column("ui_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    ui_section = Column("ui_section", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_key = Column("ui_key", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_value = Column("ui_value", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_active = Column("ui_active", Boolean(), nullable=True, unique=None, default=True)


    @classmethod
    def get_by_key(cls, key):
        return Session.query(cls).filter(cls.ui_key == key)


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
    repo_to_perm = relationship('RepoToPerm', primaryjoin='RepoToPerm.user_id==User.user_id', cascade='all')

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
    def by_username(cls, username, case_insensitive=False):
        if case_insensitive:
            return Session.query(cls).filter(cls.username.like(username)).one()
        else:
            return Session.query(cls).filter(cls.username == username).one()

    def update_lastlogin(self):
        """Update user lastlogin"""

        self.last_login = datetime.datetime.now()
        Session.add(self)
        Session.commit()
        log.debug('updated user %s lastlogin', self.username)


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
        q = Session.query(cls).filter(cls.repo_name == repo_name)

        q = q.options(joinedload(Repository.fork))\
            .options(joinedload(Repository.user))\
            .options(joinedload(Repository.group))\

        return q.one()

    @classmethod
    def get_repo_forks(cls, repo_id):
        return Session.query(cls).filter(Repository.fork_id == repo_id)

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

    @LazyProperty
    def repo_path(self):
        """
        Returns base full path for that repository means where it actually
        exists on a filesystem
        """
        q = Session.query(RhodeCodeUi).filter(RhodeCodeUi.ui_key == '/')
        q.options(FromCache("sql_cache_short", "repository_repo_path"))
        return q.one().ui_value

    @property
    def repo_full_path(self):
        p = [self.repo_path]
        # we need to split the name by / since this is how we store the
        # names in the database, but that eventually needs to be converted
        # into a valid system path
        p += self.repo_name.split('/')
        return os.path.join(*p)

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


        ret = Session.query(RhodeCodeUi)\
            .options(FromCache("sql_cache_short",
                               "repository_repo_ui")).all()

        hg_ui = ret
        for ui_ in hg_ui:
            if ui_.ui_active:
                log.debug('settings ui from db[%s]%s:%s', ui_.ui_section,
                          ui_.ui_key, ui_.ui_value)
                baseui.setconfig(ui_.ui_section, ui_.ui_key, ui_.ui_value)

        return baseui

    #==========================================================================
    # SCM CACHE INSTANCE
    #==========================================================================

    @property
    def invalidate(self):
        """
        Returns Invalidation object if this repo should be invalidated
        None otherwise. `cache_active = False` means that this cache
        state is not valid and needs to be invalidated
        """
        return Session.query(CacheInvalidation)\
            .filter(CacheInvalidation.cache_key == self.repo_name)\
            .filter(CacheInvalidation.cache_active == False)\
            .scalar()

    @property
    def set_invalidate(self):
        """
        set a cache for invalidation for this instance
        """
        inv = Session.query(CacheInvalidation)\
            .filter(CacheInvalidation.cache_key == self.repo_name)\
            .scalar()

        if inv is None:
            inv = CacheInvalidation(self.repo_name)
        inv.cache_active = True
        Session.add(inv)
        Session.commit()

    @property
    def scm_instance(self):
        return self.__get_instance()

    @property
    def scm_instance_cached(self):
        @cache_region('long_term')
        def _c(repo_name):
            return self.__get_instance()

        inv = self.invalidate
        if inv:
            region_invalidate(_c, None, self.repo_name)
            #update our cache
            inv.cache_key.cache_active = True
            Session.add(inv)
            Session.commit()

        return _c(self.repo_name)

    def __get_instance(self):

        repo_full_path = self.repo_full_path

        try:
            alias = get_scm(repo_full_path)[0]
            log.debug('Creating instance of %s repository', alias)
            backend = get_backend(alias)
        except VCSError:
            log.error(traceback.format_exc())
            log.error('Perhaps this repository is in db and not in '
                      'filesystem run rescan repositories with '
                      '"destroy old data " option from admin panel')
            return

        if alias == 'hg':
            repo = backend(repo_full_path, create=False,
                           baseui=self._ui)
            #skip hidden web repository
            if repo._get_hidden():
                return
        else:
            repo = backend(repo_full_path, create=False)

        return repo


class Group(Base, BaseModel):
    __tablename__ = 'groups'
    __table_args__ = (UniqueConstraint('group_name', 'group_parent_id'),
                      CheckConstraint('group_id != group_parent_id'), {'extend_existing':True},)
    __mapper_args__ = {'order_by':'group_name'}

    group_id = Column("group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    group_name = Column("group_name", String(length=255, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    group_parent_id = Column("group_parent_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=None, default=None)
    group_description = Column("group_description", String(length=10000, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    parent_group = relationship('Group', remote_side=group_id)


    def __init__(self, group_name='', parent_group=None):
        self.group_name = group_name
        self.parent_group = parent_group

    def __repr__(self):
        return "<%s('%s:%s')>" % (self.__class__.__name__, self.group_id,
                                  self.group_name)

    @classmethod
    def url_sep(cls):
        return '/'

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
        return Session.query(Group).filter(Group.parent_group == self)

    @property
    def full_path(self):
        return Group.url_sep().join([g.group_name for g in self.parents] +
                        [self.group_name])

    @property
    def repositories(self):
        return Session.query(Repository).filter(Repository.group == self)

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
        return Session.query(cls).filter(cls.permission_name == key).scalar()

class RepoToPerm(Base, BaseModel):
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


class UsersGroupToPerm(Base, BaseModel):
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


class GroupToPerm(Base, BaseModel):
    __tablename__ = 'group_to_perm'
    __table_args__ = (UniqueConstraint('group_id', 'permission_id'), {'extend_existing':True})

    group_to_perm_id = Column("group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)

    user = relationship('User')
    permission = relationship('Permission')
    group = relationship('Group')

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
        return Session.query(cls).filter(cls.follows_repo_id == repo_id)

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

class DbMigrateVersion(Base, BaseModel):
    __tablename__ = 'db_migrate_version'
    __table_args__ = {'extend_existing':True}
    repository_id = Column('repository_id', String(250), primary_key=True)
    repository_path = Column('repository_path', Text)
    version = Column('version', Integer)
