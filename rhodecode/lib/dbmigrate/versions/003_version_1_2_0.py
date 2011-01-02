import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper
from sqlalchemy.orm.session import Session


from rhodecode.lib.dbmigrate.migrate import *
from rhodecode.lib.dbmigrate.migrate.changeset import *

from rhodecode.model.meta import Base
from rhodecode.model.db import BaseModel

log = logging.getLogger(__name__)

def upgrade(migrate_engine):
    """ Upgrade operations go here. 
    Don't create your own engine; bind migrate_engine to your metadata
    """

    #==========================================================================
    # Add table `groups``
    #==========================================================================
    from rhodecode.model.db import Group
    Group().__table__.create()

    #==========================================================================
    # Add table `group_to_perm`
    #==========================================================================
    from rhodecode.model.db import GroupToPerm
    GroupToPerm().__table__.create()

    #==========================================================================
    # Upgrade of `repositories` table
    #==========================================================================    
    tblname = 'repositories'
    tbl = Table(tblname, MetaData(bind=migrate_engine), autoload=True,
                    autoload_with=migrate_engine)

    #ADD group_id column#
    group_id = Column("group_id", Integer(), #ForeignKey('groups.group_id'),
                  nullable=True, unique=False, default=None)

    group_id.create(tbl)

# TODO: fix this somehow ?!
#    cons = ForeignKeyConstraint([tbl.c.group_id], ['groups.group_id'], table=tbl)
#
#    cons.create()
    return


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


