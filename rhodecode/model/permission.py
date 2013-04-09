# -*- coding: utf-8 -*-
"""
    rhodecode.model.permission
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    permissions model for RhodeCode

    :created_on: Aug 20, 2010
    :author: marcink
    :copyright: (C) 2010-2012 Marcin Kuzminski <marcin@python-works.com>
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
import traceback

from sqlalchemy.exc import DatabaseError

from rhodecode.model import BaseModel
from rhodecode.model.db import User, Permission, UserToPerm, UserRepoToPerm,\
    UserRepoGroupToPerm
from rhodecode.lib.utils2 import str2bool

log = logging.getLogger(__name__)


class PermissionModel(BaseModel):
    """
    Permissions model for RhodeCode
    """

    cls = Permission

    def update(self, form_result):
        perm_user = User.get_by_username(username=form_result['perm_user_name'])
        u2p = self.sa.query(UserToPerm).filter(UserToPerm.user == perm_user).all()

        try:
            def _make_new(usr, perm_name):
                new = UserToPerm()
                new.user = usr
                new.permission = Permission.get_by_key(perm_name)
                return new
            # clear current entries, to make this function idempotent
            # it will fix even if we define more permissions or permissions
            # are somehow missing
            for p in u2p:
                self.sa.delete(p)
            #create fresh set of permissions
            for def_perm_key in ['default_repo_perm', 'default_group_perm',
                                 'default_register', 'default_create',
                                 'default_fork']:
                p = _make_new(perm_user, form_result[def_perm_key])
                self.sa.add(p)

            #stage 2 update all default permissions for repos if checked
            if form_result['overwrite_default_repo'] == True:
                _def_name = form_result['default_repo_perm'].split('repository.')[-1]
                _def = Permission.get_by_key('repository.' + _def_name)
                # repos
                for r2p in self.sa.query(UserRepoToPerm)\
                               .filter(UserRepoToPerm.user == perm_user)\
                               .all():

                    #don't reset PRIVATE repositories
                    if not r2p.repository.private:
                        r2p.permission = _def
                        self.sa.add(r2p)

            if form_result['overwrite_default_group'] == True:
                _def_name = form_result['default_group_perm'].split('group.')[-1]
                # groups
                _def = Permission.get_by_key('group.' + _def_name)
                for g2p in self.sa.query(UserRepoGroupToPerm)\
                               .filter(UserRepoGroupToPerm.user == perm_user)\
                               .all():
                    g2p.permission = _def
                    self.sa.add(g2p)

            # stage 3 set anonymous access
            if perm_user.username == 'default':
                perm_user.active = str2bool(form_result['anonymous'])
                self.sa.add(perm_user)

            self.sa.commit()
        except (DatabaseError,):
            log.error(traceback.format_exc())
            self.sa.rollback()
            raise
