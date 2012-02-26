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

    #==========================================================================
    # Change unique constraints of table `repo_to_perm`
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import UserRepoToPerm
    tbl = UserRepoToPerm().__table__
    new_cons = UniqueConstraint('user_id', 'repository_id', 'permission_id', table=tbl)
    new_cons.create()
    old_cons = None
    if migrate_engine.name in ['mysql']:
        old_cons = UniqueConstraint('user_id', 'repository_id', table=tbl, name="user_id")
    elif migrate_engine.name in ['postgresql']:
        old_cons = UniqueConstraint('user_id', 'repository_id', table=tbl)
    else:
        # sqlite doesn't support dropping constraints...
        print """Please manually drop UniqueConstraint('user_id', 'repository_id')"""

    if old_cons:
        try:
            old_cons.drop()
        except Exception, e:
            # we don't care if this fails really... better to pass migration than
            # leave this in intermidiate state
            print 'Failed to remove Unique for user_id, repository_id reason %s' % e


    #==========================================================================
    # fix uniques of table `user_repo_group_to_perm`
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import UserRepoGroupToPerm
    tbl = UserRepoGroupToPerm().__table__
    new_cons = UniqueConstraint('group_id', 'permission_id', 'user_id', table=tbl)
    new_cons.create()
    old_cons = None

    # fix uniqueConstraints
    if migrate_engine.name in ['mysql']:
        #mysql is givinig troubles here...
        old_cons = UniqueConstraint('group_id', 'permission_id', table=tbl, name="group_id")
    elif migrate_engine.name in ['postgresql']:
        old_cons = UniqueConstraint('group_id', 'permission_id', table=tbl, name='group_to_perm_group_id_permission_id_key')
    else:
        # sqlite doesn't support dropping constraints...
        print """Please manually drop UniqueConstraint('group_id', 'permission_id')"""

    if old_cons:
        try:
            old_cons.drop()
        except Exception, e:
            # we don't care if this fails really... better to pass migration than
            # leave this in intermidiate state
            print 'Failed to remove Unique for user_id, repository_id reason %s' % e

    return


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
