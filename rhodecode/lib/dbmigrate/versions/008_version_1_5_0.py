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
    from rhodecode.lib.dbmigrate.schema.db_1_5_0 import UserLog
    tbl = UserLog.__table__
    username = Column("username", String(255, convert_unicode=False,
                                         assert_unicode=None), nullable=True,
                      unique=None, default=None)
    # create username column
    username.create(table=tbl)

    ## after adding that column fix all usernames
    users_log = UserLog.query()\
            .options(joinedload(UserLog.user))\
            .options(joinedload(UserLog.repository)).all()
    for entry in users_log:
        entry.username = entry.user.username
        Session().add(entry)
    Session().commit()


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
