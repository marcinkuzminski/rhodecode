import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

from rhodecode.lib.dbmigrate.migrate import *
from rhodecode.lib.dbmigrate.migrate.changeset import *

from rhodecode.model.meta import Base
from rhodecode.model import meta

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """

    #==========================================================================
    # USEREMAILMAP
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_4_0 import UserEmailMap
    tbl = UserEmailMap.__table__
    tbl.create()
    #==========================================================================
    # PULL REQUEST
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_4_0 import PullRequest
    tbl = PullRequest.__table__
    tbl.create()

    #==========================================================================
    # PULL REQUEST REVIEWERS
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_4_0 import PullRequestReviewers
    tbl = PullRequestReviewers.__table__
    tbl.create()

    #==========================================================================
    # CHANGESET STATUS
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_4_0 import ChangesetStatus
    tbl = ChangesetStatus.__table__
    tbl.create()

    ## RESET COMPLETLY THE metadata for sqlalchemy to use the 1_3_0 Base
    Base = declarative_base()
    Base.metadata.clear()
    Base.metadata = MetaData()
    Base.metadata.bind = migrate_engine
    meta.Base = Base

    #==========================================================================
    # USERS TABLE
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import User
    tbl = User.__table__

    # change column name -> firstname
    col = User.__table__.columns.name
    col.alter(index=Index('u_username_idx', 'username'))
    col.alter(index=Index('u_email_idx', 'email'))
    col.alter(name="firstname", table=tbl)

    # add inherit_default_permission column
    inherit_default_permissions = Column("inherit_default_permissions",
                                         Boolean(), nullable=True, unique=None,
                                         default=True)
    inherit_default_permissions.create(table=tbl)
    inherit_default_permissions.alter(nullable=False, default=True, table=tbl)

    #==========================================================================
    # USERS GROUP TABLE
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import UsersGroup
    tbl = UsersGroup.__table__
    # add inherit_default_permission column
    gr_inherit_default_permissions = Column(
                                    "users_group_inherit_default_permissions",
                                    Boolean(), nullable=True, unique=None,
                                    default=True)
    gr_inherit_default_permissions.create(table=tbl)
    gr_inherit_default_permissions.alter(nullable=False, default=True, table=tbl)

    #==========================================================================
    # REPOSITORIES
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import Repository
    tbl = Repository.__table__

    # add enable locking column
    enable_locking = Column("enable_locking", Boolean(), nullable=True,
                            unique=None, default=False)
    enable_locking.create(table=tbl)
    enable_locking.alter(nullable=False, default=False, table=tbl)

    # add locked column
    _locked = Column("locked", String(255), nullable=True, unique=False,
                     default=None)
    _locked.create(table=tbl)

    #add langing revision column
    landing_rev = Column("landing_revision", String(255), nullable=True,
                         unique=False, default='tip')
    landing_rev.create(table=tbl)
    landing_rev.alter(nullable=False, default='tip', table=tbl)

    #==========================================================================
    # GROUPS
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import RepoGroup
    tbl = RepoGroup.__table__

    # add enable locking column
    enable_locking = Column("enable_locking", Boolean(), nullable=True,
                            unique=None, default=False)
    enable_locking.create(table=tbl)
    enable_locking.alter(nullable=False, default=False)

    #==========================================================================
    # CACHE INVALIDATION
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import CacheInvalidation
    tbl = CacheInvalidation.__table__

    # add INDEX for cache keys
    col = CacheInvalidation.__table__.columns.cache_key
    col.alter(index=Index('key_idx', 'cache_key'))

    #==========================================================================
    # NOTIFICATION
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import Notification
    tbl = Notification.__table__

    # add index for notification type
    col = Notification.__table__.columns.type
    col.alter(index=Index('notification_type_idx', 'type'),)

    #==========================================================================
    # CHANGESET_COMMENTS
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import ChangesetComment

    tbl = ChangesetComment.__table__
    col = ChangesetComment.__table__.columns.revision

    # add index for revisions
    col.alter(index=Index('cc_revision_idx', 'revision'),)

    # add hl_lines column
    hl_lines = Column('hl_lines', Unicode(512), nullable=True)
    hl_lines.create(table=tbl)

    # add created_on column
    created_on = Column('created_on', DateTime(timezone=False), nullable=True,
                        default=datetime.datetime.now)
    created_on.create(table=tbl)
    created_on.alter(nullable=False, default=datetime.datetime.now)

    modified_at = Column('modified_at', DateTime(timezone=False), nullable=False,
                         default=datetime.datetime.now)
    modified_at.alter(type=DateTime(timezone=False), table=tbl)

    # add FK to pull_request
    pull_request_id = Column("pull_request_id", Integer(),
                             ForeignKey('pull_requests.pull_request_id'),
                             nullable=True)
    pull_request_id.create(table=tbl)
    ## RESET COMPLETLY THE metadata for sqlalchemy back after using 1_3_0
    Base = declarative_base()
    Base.metadata.clear()
    Base.metadata = MetaData()
    Base.metadata.bind = migrate_engine
    meta.Base = Base


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
