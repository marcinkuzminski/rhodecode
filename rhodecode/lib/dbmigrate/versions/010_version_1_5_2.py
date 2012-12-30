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


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
