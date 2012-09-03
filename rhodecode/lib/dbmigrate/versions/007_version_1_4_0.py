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
    # CHANGESET_COMMENTS
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_4_0 import ChangesetComment
    tbl_name = ChangesetComment.__tablename__
    tbl = Table(tbl_name,
                MetaData(bind=migrate_engine), autoload=True,
                autoload_with=migrate_engine)
    col = tbl.columns.revision

    # remove nullability from revision field
    col.alter(nullable=True)

    #==========================================================================
    # REPOSITORY
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_4_0 import Repository
    tbl = Repository.__table__
    updated_on = Column('updated_on', DateTime(timezone=False),
                        nullable=True, unique=None)
    # create created on column for future lightweight main page
    updated_on.create(table=tbl)


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
