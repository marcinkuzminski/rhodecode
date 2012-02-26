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

    if migrate_engine.name in ['mysql']:
        old_cons = UniqueConstraint('user_id', 'repository_id', table=tbl, name="user_id")
        old_cons.drop()
    elif migrate_engine.name in ['postgresql']:
        old_cons = UniqueConstraint('user_id', 'repository_id', table=tbl)
        old_cons.drop()
    else:
        # sqlite doesn't support dropping constraints...
        print """Please manually drop UniqueConstraint('user_id', 'repository_id')"""

    #==========================================================================
    # fix uniques of table `user_repo_group_to_perm`
    #==========================================================================
    from rhodecode.lib.dbmigrate.schema.db_1_3_0 import UserRepoGroupToPerm
    tbl = UserRepoGroupToPerm().__table__
    new_cons = UniqueConstraint('group_id', 'permission_id', 'user_id', table=tbl)
    new_cons.create()

    # fix uniqueConstraints
    if migrate_engine.name in ['mysql']:
        #mysql is givinig troubles here...
        old_cons = UniqueConstraint('group_id', 'permission_id', table=tbl, name="group_id")
        old_cons.drop()
    elif migrate_engine.name in ['postgresql']:
        old_cons = UniqueConstraint('group_id', 'permission_id', table=tbl, name='group_to_perm_group_id_permission_id_key')
        old_cons.drop()
    else:
        # sqlite doesn't support dropping constraints...
        print """Please manually drop UniqueConstraint('group_id', 'permission_id')"""

    return


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
