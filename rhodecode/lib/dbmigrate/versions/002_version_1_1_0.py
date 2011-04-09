import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper
from sqlalchemy.orm.session import Session
from rhodecode.model.meta import Base

from rhodecode.lib.dbmigrate.migrate import *
from rhodecode.lib.dbmigrate.migrate.changeset import *

log = logging.getLogger(__name__)

def upgrade(migrate_engine):
    """ Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """

    #==========================================================================
    # Upgrade of `users` table
    #==========================================================================
    tblname = 'users'
    tbl = Table(tblname, MetaData(bind=migrate_engine), autoload=True,
                    autoload_with=migrate_engine)

    #ADD is_ldap column
    is_ldap = Column("is_ldap", Boolean(), nullable=True,
                     unique=None, default=False)
    is_ldap.create(tbl, populate_default=True)
    is_ldap.alter(nullable=False)

    #==========================================================================
    # Upgrade of `user_logs` table
    #==========================================================================

    tblname = 'users'
    tbl = Table(tblname, MetaData(bind=migrate_engine), autoload=True,
                    autoload_with=migrate_engine)

    #ADD revision column
    revision = Column('revision', TEXT(length=None, convert_unicode=False,
                                       assert_unicode=None),
                      nullable=True, unique=None, default=None)
    revision.create(tbl)



    #==========================================================================
    # Upgrade of `repositories` table
    #==========================================================================
    tblname = 'repositories'
    tbl = Table(tblname, MetaData(bind=migrate_engine), autoload=True,
                    autoload_with=migrate_engine)

    #ADD repo_type column#
    repo_type = Column("repo_type", String(length=None, convert_unicode=False,
                                           assert_unicode=None),
                       nullable=True, unique=False, default='hg')

    repo_type.create(tbl, populate_default=True)
    #repo_type.alter(nullable=False)

    #ADD statistics column#
    enable_statistics = Column("statistics", Boolean(), nullable=True,
                               unique=None, default=True)
    enable_statistics.create(tbl)

    #==========================================================================
    # Add table `user_followings`
    #==========================================================================
    class UserFollowing(Base, BaseModel):
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

    UserFollowing().__table__.create()

    #==========================================================================
    # Add table `cache_invalidation`
    #==========================================================================
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
            return "<CacheInvalidation('%s:%s')>" % (self.cache_id, self.cache_key)
    CacheInvalidation().__table__.create()

    return

def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
