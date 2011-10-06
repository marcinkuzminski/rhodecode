#==============================================================================
# DB INITIAL MODEL
#==============================================================================
import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper
from sqlalchemy.orm.session import Session
from rhodecode.model.meta import Base

from rhodecode.lib.dbmigrate.migrate import *

log = logging.getLogger(__name__)

class RhodeCodeSettings(Base):
    __tablename__ = 'rhodecode_settings'
    __table_args__ = (UniqueConstraint('app_settings_name'), {'useexisting':True})
    app_settings_id = Column("app_settings_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    app_settings_name = Column("app_settings_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    app_settings_value = Column("app_settings_value", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __init__(self, k, v):
        self.app_settings_name = k
        self.app_settings_value = v

    def __repr__(self):
        return "<RhodeCodeSetting('%s:%s')>" % (self.app_settings_name,
                                                self.app_settings_value)

class RhodeCodeUi(Base):
    __tablename__ = 'rhodecode_ui'
    __table_args__ = {'useexisting':True}
    ui_id = Column("ui_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    ui_section = Column("ui_section", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_key = Column("ui_key", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_value = Column("ui_value", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ui_active = Column("ui_active", Boolean(), nullable=True, unique=None, default=True)


class User(Base):
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
    is_ldap = Column("is_ldap", Boolean(), nullable=False, unique=None, default=False)

    user_log = relation('UserLog', cascade='all')
    user_perms = relation('UserToPerm', primaryjoin="User.user_id==UserToPerm.user_id", cascade='all')

    repositories = relation('Repository')
    user_followers = relation('UserFollowing', primaryjoin='UserFollowing.follows_user_id==User.user_id', cascade='all')

    @property
    def full_contact(self):
        return '%s %s <%s>' % (self.name, self.lastname, self.email)

    def __repr__(self):
        return "<User('id:%s:%s')>" % (self.user_id, self.username)

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
    user_id = Column("user_id", Integer(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(length=None, convert_unicode=False, assert_unicode=None), ForeignKey(u'repositories.repo_id'), nullable=False, unique=None, default=None)
    repository_name = Column("repository_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    user_ip = Column("user_ip", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action = Column("action", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    action_date = Column("action_date", DateTime(timezone=False), nullable=True, unique=None, default=None)

    user = relation('User')
    repository = relation('Repository')

class Repository(Base):
    __tablename__ = 'repositories'
    __table_args__ = (UniqueConstraint('repo_name'), {'useexisting':True},)
    repo_id = Column("repo_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repo_name = Column("repo_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
    repo_type = Column("repo_type", String(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=False, default=None)
    user_id = Column("user_id", Integer(), ForeignKey(u'users.user_id'), nullable=False, unique=False, default=None)
    private = Column("private", Boolean(), nullable=True, unique=None, default=None)
    enable_statistics = Column("statistics", Boolean(), nullable=True, unique=None, default=True)
    description = Column("description", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    fork_id = Column("fork_id", Integer(), ForeignKey(u'repositories.repo_id'), nullable=True, unique=False, default=None)

    user = relation('User')
    fork = relation('Repository', remote_side=repo_id)
    repo_to_perm = relation('RepoToPerm', cascade='all')
    stats = relation('Statistics', cascade='all', uselist=False)

    repo_followers = relation('UserFollowing', primaryjoin='UserFollowing.follows_repo_id==Repository.repo_id', cascade='all')


    def __repr__(self):
        return "<Repository('%s:%s')>" % (self.repo_id, self.repo_name)

class Permission(Base):
    __tablename__ = 'permissions'
    __table_args__ = {'useexisting':True}
    permission_id = Column("permission_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    permission_name = Column("permission_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    permission_longname = Column("permission_longname", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)

    def __repr__(self):
        return "<Permission('%s:%s')>" % (self.permission_id, self.permission_name)

class RepoToPerm(Base):
    __tablename__ = 'repo_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'repository_id'), {'useexisting':True})
    repo_to_perm_id = Column("repo_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey(u'permissions.permission_id'), nullable=False, unique=None, default=None)
    repository_id = Column("repository_id", Integer(), ForeignKey(u'repositories.repo_id'), nullable=False, unique=None, default=None)

    user = relation('User')
    permission = relation('Permission')
    repository = relation('Repository')

class UserToPerm(Base):
    __tablename__ = 'user_to_perm'
    __table_args__ = (UniqueConstraint('user_id', 'permission_id'), {'useexisting':True})
    user_to_perm_id = Column("user_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    permission_id = Column("permission_id", Integer(), ForeignKey(u'permissions.permission_id'), nullable=False, unique=None, default=None)

    user = relation('User')
    permission = relation('Permission')

class Statistics(Base):
    __tablename__ = 'statistics'
    __table_args__ = (UniqueConstraint('repository_id'), {'useexisting':True})
    stat_id = Column("stat_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    repository_id = Column("repository_id", Integer(), ForeignKey(u'repositories.repo_id'), nullable=False, unique=True, default=None)
    stat_on_revision = Column("stat_on_revision", Integer(), nullable=False)
    commit_activity = Column("commit_activity", LargeBinary(), nullable=False)#JSON data
    commit_activity_combined = Column("commit_activity_combined", LargeBinary(), nullable=False)#JSON data
    languages = Column("languages", LargeBinary(), nullable=False)#JSON data

    repository = relation('Repository', single_parent=True)

class UserFollowing(Base):
    __tablename__ = 'user_followings'
    __table_args__ = (UniqueConstraint('user_id', 'follows_repository_id'),
                      UniqueConstraint('user_id', 'follows_user_id')
                      , {'useexisting':True})

    user_following_id = Column("user_following_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey(u'users.user_id'), nullable=False, unique=None, default=None)
    follows_repo_id = Column("follows_repository_id", Integer(), ForeignKey(u'repositories.repo_id'), nullable=True, unique=None, default=None)
    follows_user_id = Column("follows_user_id", Integer(), ForeignKey(u'users.user_id'), nullable=True, unique=None, default=None)

    user = relation('User', primaryjoin='User.user_id==UserFollowing.user_id')

    follows_user = relation('User', primaryjoin='User.user_id==UserFollowing.follows_user_id')
    follows_repository = relation('Repository')


class CacheInvalidation(Base):
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
        return "<CacheInvalidation('%s:%s')>" % (self.cache_id, self.cache_key)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    Base.metadata.create_all(bind=migrate_engine, checkfirst=False)

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    Base.metadata.drop_all(bind=migrate_engine, checkfirst=False)
