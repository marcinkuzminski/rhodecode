import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper
from sqlalchemy.orm.session import Session

from rhodecode.lib.dbmigrate.migrate import *
from rhodecode.lib.dbmigrate.migrate.changeset import *

from rhodecode.model.meta import Base

log = logging.getLogger(__name__)

def upgrade(migrate_engine):
    """ Upgrade operations go here.
    Don't create your own engine; bind migrate_engine to your metadata
    """



    return


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
