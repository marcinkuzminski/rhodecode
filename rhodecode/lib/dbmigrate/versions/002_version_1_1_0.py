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
    from rhodecode.lib.dbmigrate.schema.db_1_1_0 import UserFollowing
    UserFollowing().__table__.create()

    #==========================================================================
    # Add table `cache_invalidation`
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_1_0 import CacheInvalidation
    CacheInvalidation().__table__.create()

    return


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
