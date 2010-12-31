import logging
import datetime

from sqlalchemy import *
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import relation, backref, class_mapper
from sqlalchemy.orm.session import Session
from rhodecode.model.meta import Base
from rhodecode.model.db import BaseModel

from rhodecode.lib.dbmigrate.migrate import *

log = logging.getLogger(__name__)

def upgrade(migrate_engine):
    """ Upgrade operations go here. 
    Don't create your own engine; bind migrate_engine to your metadata
    """

    #==========================================================================
    # Add table `groups``
    #==========================================================================
    tblname = 'groups'

    class Group(Base, BaseModel):
        __tablename__ = 'groups'
        __table_args__ = (UniqueConstraint('group_name'), {'useexisting':True},)

        group_id = Column("group_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
        group_name = Column("group_name", String(length=None, convert_unicode=False, assert_unicode=None), nullable=False, unique=True, default=None)
        group_parent_id = Column("group_parent_id", Integer(), ForeignKey('groups.group_id'), nullable=True, unique=None, default=None)

        parent_group = relation('Group', remote_side=group_id)


        def __init__(self, group_name='', parent_group=None):
            self.group_name = group_name
            self.parent_group = parent_group

        def __repr__(self):
            return "<%s('%s:%s')>" % (self.__class__.__name__, self.group_id,
                                      self.group_name)

    Base.metadata.tables[tblname].create(migrate_engine)

    #==========================================================================
    # Add table `group_to_perm`
    #==========================================================================
    tblname = 'group_to_perm'

    class GroupToPerm(Base, BaseModel):
        __tablename__ = 'group_to_perm'
        __table_args__ = (UniqueConstraint('group_id', 'permission_id'), {'useexisting':True})

        group_to_perm_id = Column("group_to_perm_id", Integer(), nullable=False, unique=True, default=None, primary_key=True)
        user_id = Column("user_id", Integer(), ForeignKey('users.user_id'), nullable=False, unique=None, default=None)
        permission_id = Column("permission_id", Integer(), ForeignKey('permissions.permission_id'), nullable=False, unique=None, default=None)
        group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'), nullable=False, unique=None, default=None)

        user = relation('User')
        permission = relation('Permission')
        group = relation('Group')

    Base.metadata.tables[tblname].create(migrate_engine)

    #==========================================================================
    # Upgrade of `repositories` table
    #==========================================================================    
    tblname = 'repositories'
    tbl = Table(tblname, MetaData(bind=migrate_engine), autoload=True,
                    autoload_with=migrate_engine)

    #ADD group_id column#
    group_id = Column("group_id", Integer(), ForeignKey(u'groups.group_id'),
                  nullable=True, unique=False, default=None)

    group_id.create(tbl, populate_default=True)


    return


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine


