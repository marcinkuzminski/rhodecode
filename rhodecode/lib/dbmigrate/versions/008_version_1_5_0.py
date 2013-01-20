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
    #==========================================================================
    # USER LOGS
    #==========================================================================
    _reset_base(migrate_engine)
    from rhodecode.lib.dbmigrate.schema.db_1_5_0 import UserLog
    tbl = UserLog.__table__
    username = Column("username", String(255, convert_unicode=False,
                                         assert_unicode=None), nullable=True,
                      unique=None, default=None)
    # create username column
    username.create(table=tbl)

    _Session = Session()
    ## after adding that column fix all usernames
    users_log = _Session.query(UserLog)\
            .options(joinedload(UserLog.user))\
            .options(joinedload(UserLog.repository)).all()

    for entry in users_log:
        entry.username = entry.user.username
        _Session.add(entry)
    _Session.commit()

    #alter username to not null
    from rhodecode.lib.dbmigrate.schema.db_1_5_0 import UserLog
    tbl_name = UserLog.__tablename__
    tbl = Table(tbl_name,
                MetaData(bind=migrate_engine), autoload=True,
                autoload_with=migrate_engine)
    col = tbl.columns.username

    # remove nullability from revision field
    col.alter(nullable=False)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
