# -*- coding: utf-8 -*-
"""
    rhodecode.model.users_group
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    repository permission model for RhodeCode

    :created_on: Oct 1, 2011
    :author: nvinot
    :copyright: (C) 2011-2011 Nicolas Vinot <aeris@imirhil.fr>
    :license: GPLv3, see COPYING for more details.
"""
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from rhodecode.model.db import BaseModel, RepoToPerm, Permission
from rhodecode.model.meta import Session

log = logging.getLogger( __name__ )

class RepositoryPermissionModel( BaseModel ):
    def getUserPermission( self, repository, user ):
        return RepoToPerm.query() \
                .filter( RepoToPerm.user == user ) \
                .filter( RepoToPerm.repository == repository ) \
                .scalar()

    def updateUserPermission( self, repository, user, permission ):
        permission = Permission.get_by_key( permission )
        current = self.getUserPermission( repository, user )
        if current:
            if not current.permission is permission:
                current.permission = permission
        else:
            p = RepoToPerm()
            p.user = user
            p.repository = repository
            p.permission = permission
            Session.add( p )
        Session.commit()

    def deleteUserPermission( self, repository, user ):
        current = self.getUserPermission( repository, user )
        if current:
            Session.delete( current )
            Session.commit()

    def updateOrDeleteUserPermission( self, repository, user, permission ):
        if permission:
            self.updateUserPermission( repository, user, permission )
        else:
            self.deleteUserPermission( repository, user )
