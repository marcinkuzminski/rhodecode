import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper, joinedload
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative import declarative_base

from rhodecode.lib.dbmigrate.migrate import *
from rhodecode.lib.dbmigrate.migrate.changeset import *

from rhodecode.model.meta import Base
from rhodecode.model import meta
from rhodecode.lib.dbmigrate.versions import _reset_base

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    _reset_base(migrate_engine)
    #==========================================================================
    # USER LOGS
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_5_2 import UserIpMap
    tbl = UserIpMap.__table__
    tbl.create()

    #==========================================================================
    # REPOSITORIES
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_5_2 import Repository
    tbl = Repository.__table__
    changeset_cache = Column("changeset_cache", LargeBinary(), nullable=True)
    # create username column
    changeset_cache.create(table=tbl)

    #fix cache data
    repositories = Repository.getAll()
    for entry in repositories:
        entry.update_changeset_cache()


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
