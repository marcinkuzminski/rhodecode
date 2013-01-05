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

log = logging.getLogger(__name__)


def upgrade(migrate_engine):
    """
    Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """
    #==========================================================================
    # USER LOGS
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_5_0 import UserIpMap
    tbl = UserIpMap.__table__
    tbl.create()

    #==========================================================================
    # REPOSITORIES
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_5_0 import Repository
    tbl = Repository.__table__
    changeset_cache = Column("changeset_cache", LargeBinary(), nullable=True)
    # create username column
    changeset_cache.create(table=tbl)

    #fix cache data
    _Session = Session()
    ## after adding that column fix all usernames
    repositories = _Session.query(Repository).all()
    for entry in repositories:
        entry.update_changeset_cache()
    _Session.commit()


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
