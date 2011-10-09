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
    # Add table `users_groups`
    #==========================================================================
    from rhodecode.model.db import UsersGroup
    UsersGroup().__table__.create()

    #==========================================================================
    # Add table `users_groups_members`
    #==========================================================================
    from rhodecode.model.db import UsersGroupMember
    UsersGroupMember().__table__.create()

    #==========================================================================
    # Add table `users_group_repo_to_perm`
    #==========================================================================
    from rhodecode.model.db import UsersGroupRepoToPerm
    UsersGroupRepoToPerm().__table__.create()

    #==========================================================================
    # Add table `users_group_to_perm`
    #==========================================================================
    from rhodecode.model.db import UsersGroupToPerm
    UsersGroupToPerm().__table__.create()

    #==========================================================================
    # Upgrade of `users` table
    #==========================================================================
    from rhodecode.model.db import User

    #add column
    ldap_dn = Column("ldap_dn", String(length=None, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    ldap_dn.create(User().__table__)

    api_key = Column("api_key", String(length=255, convert_unicode=False, assert_unicode=None), nullable=True, unique=None, default=None)
    api_key.create(User().__table__)

    #remove old column
    is_ldap = Column("is_ldap", Boolean(), nullable=False, unique=None, default=False)
    is_ldap.drop(User().__table__)


    #==========================================================================
    # Upgrade of `repositories` table
    #==========================================================================
    from rhodecode.model.db import Repository

    #ADD clone_uri column#

    clone_uri = Column("clone_uri", String(length=255, convert_unicode=False,
                                           assert_unicode=None),
                        nullable=True, unique=False, default=None)

    clone_uri.create(Repository().__table__)
    
    #ADD downloads column#
    enable_downloads = Column("downloads", Boolean(), nullable=True, unique=None, default=True)
    enable_downloads.create(Repository().__table__)

    #ADD column created_on
    created_on = Column('created_on', DateTime(timezone=False), nullable=True,
                        unique=None, default=datetime.datetime.now)
    created_on.create(Repository().__table__)

    #ADD group_id column#
    group_id = Column("group_id", Integer(), ForeignKey('groups.group_id'),
                  nullable=True, unique=False, default=None)

    group_id.create(Repository().__table__)


    #==========================================================================
    # Upgrade of `user_followings` table
    #==========================================================================

    from rhodecode.model.db import UserFollowing

    follows_from = Column('follows_from', DateTime(timezone=False), 
                          nullable=True, unique=None, 
                          default=datetime.datetime.now)
    follows_from.create(UserFollowing().__table__)

    return


def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine
