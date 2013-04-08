# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.users_groups
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    User Groups crud controller for pylons

    :created_on: Jan 25, 2011
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
import formencode

from formencode import htmlfill
from pylons import request, session, tmpl_context as c, url, config
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from rhodecode.lib import helpers as h
from rhodecode.lib.exceptions import UserGroupsAssignedException
from rhodecode.lib.utils2 import safe_unicode, str2bool
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator
from rhodecode.lib.base import BaseController, render

from rhodecode.model.users_group import UserGroupModel

from rhodecode.model.db import User, UserGroup, UserGroupToPerm,\
    UserGroupRepoToPerm, UserGroupRepoGroupToPerm
from rhodecode.model.forms import UserGroupForm
from rhodecode.model.meta import Session
from rhodecode.lib.utils import action_logger
from sqlalchemy.orm import joinedload

log = logging.getLogger(__name__)


class UsersGroupsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('users_group', 'users_groups')

    @LoginRequired()
    @HasPermissionAllDecorator('hg.admin')
    def __before__(self):
        super(UsersGroupsController, self).__before__()
        c.available_permissions = config['available_permissions']

    def index(self, format='html'):
        """GET /users_groups: All items in the collection"""
        # url('users_groups')
        c.users_groups_list = UserGroup().query().all()
        return render('admin/users_groups/users_groups.html')

    def create(self):
        """POST /users_groups: Create a new item"""
        # url('users_groups')

        users_group_form = UserGroupForm()()
        try:
            form_result = users_group_form.to_python(dict(request.POST))
            UserGroupModel().create(name=form_result['users_group_name'],
                                     active=form_result['users_group_active'])
            gr = form_result['users_group_name']
            action_logger(self.rhodecode_user,
                          'admin_created_users_group:%s' % gr,
                          None, self.ip_addr, self.sa)
            h.flash(_('Created user group %s') % gr, category='success')
            Session().commit()
        except formencode.Invalid, errors:
            return htmlfill.render(
                render('admin/users_groups/users_group_add.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('Error occurred during creation of user group %s') \
                    % request.POST.get('users_group_name'), category='error')

        return redirect(url('users_groups'))

    def new(self, format='html'):
        """GET /users_groups/new: Form to create a new item"""
        # url('new_users_group')
        return render('admin/users_groups/users_group_add.html')

    def _load_data(self, id):
        c.users_group.permissions = {
            'repositories': {},
            'repositories_groups': {}
        }

        ugroup_repo_perms = UserGroupRepoToPerm.query()\
            .options(joinedload(UserGroupRepoToPerm.permission))\
            .options(joinedload(UserGroupRepoToPerm.repository))\
            .filter(UserGroupRepoToPerm.users_group_id == id)\
            .all()

        for gr in ugroup_repo_perms:
            c.users_group.permissions['repositories'][gr.repository.repo_name]  \
                = gr.permission.permission_name

        ugroup_group_perms = UserGroupRepoGroupToPerm.query()\
            .options(joinedload(UserGroupRepoGroupToPerm.permission))\
            .options(joinedload(UserGroupRepoGroupToPerm.group))\
            .filter(UserGroupRepoGroupToPerm.users_group_id == id)\
            .all()

        for gr in ugroup_group_perms:
            c.users_group.permissions['repositories_groups'][gr.group.group_name] \
                = gr.permission.permission_name

        c.group_members_obj = sorted((x.user for x in c.users_group.members),
                                     key=lambda u: u.username.lower())
        c.group_members = [(x.user_id, x.username) for x in
                           c.group_members_obj]
        c.available_members = sorted(((x.user_id, x.username) for x in
                                      User.query().all()),
                                     key=lambda u: u[1].lower())

    def update(self, id):
        """PUT /users_groups/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('users_group', id=ID),
        #           method='put')
        # url('users_group', id=ID)

        c.users_group = UserGroup.get_or_404(id)
        self._load_data(id)

        available_members = [safe_unicode(x[0]) for x in c.available_members]

        users_group_form = UserGroupForm(edit=True,
                                          old_data=c.users_group.get_dict(),
                                          available_members=available_members)()

        try:
            form_result = users_group_form.to_python(request.POST)
            UserGroupModel().update(c.users_group, form_result)
            gr = form_result['users_group_name']
            action_logger(self.rhodecode_user,
                          'admin_updated_users_group:%s' % gr,
                          None, self.ip_addr, self.sa)
            h.flash(_('Updated user group %s') % gr, category='success')
            Session().commit()
        except formencode.Invalid, errors:
            ug_model = UserGroupModel()
            defaults = errors.value
            e = errors.error_dict or {}
            defaults.update({
                'create_repo_perm': ug_model.has_perm(id,
                                                      'hg.create.repository'),
                'fork_repo_perm': ug_model.has_perm(id,
                                                    'hg.fork.repository'),
                '_method': 'put'
            })

            return htmlfill.render(
                render('admin/users_groups/users_group_edit.html'),
                defaults=defaults,
                errors=e,
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('Error occurred during update of user group %s') \
                    % request.POST.get('users_group_name'), category='error')

        return redirect(url('edit_users_group', id=id))

    def delete(self, id):
        """DELETE /users_groups/id: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('users_group', id=ID),
        #           method='delete')
        # url('users_group', id=ID)
        usr_gr = UserGroup.get_or_404(id)
        try:
            UserGroupModel().delete(usr_gr)
            Session().commit()
            h.flash(_('Successfully deleted user group'), category='success')
        except UserGroupsAssignedException, e:
            h.flash(e, category='error')
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during deletion of user group'),
                    category='error')
        return redirect(url('users_groups'))

    def show(self, id, format='html'):
        """GET /users_groups/id: Show a specific item"""
        # url('users_group', id=ID)

    def edit(self, id, format='html'):
        """GET /users_groups/id/edit: Form to edit an existing item"""
        # url('edit_users_group', id=ID)

        c.users_group = UserGroup.get_or_404(id)
        self._load_data(id)

        ug_model = UserGroupModel()
        defaults = c.users_group.get_dict()
        defaults.update({
            'create_repo_perm': ug_model.has_perm(c.users_group,
                                                  'hg.create.repository'),
            'fork_repo_perm': ug_model.has_perm(c.users_group,
                                                'hg.fork.repository'),
        })

        return htmlfill.render(
            render('admin/users_groups/users_group_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    def update_perm(self, id):
        """PUT /users_perm/id: Update an existing item"""
        # url('users_group_perm', id=ID, method='put')

        users_group = UserGroup.get_or_404(id)
        grant_create_perm = str2bool(request.POST.get('create_repo_perm'))
        grant_fork_perm = str2bool(request.POST.get('fork_repo_perm'))
        inherit_perms = str2bool(request.POST.get('inherit_default_permissions'))

        usergroup_model = UserGroupModel()

        try:
            users_group.inherit_default_permissions = inherit_perms
            Session().add(users_group)

            if grant_create_perm:
                usergroup_model.revoke_perm(id, 'hg.create.none')
                usergroup_model.grant_perm(id, 'hg.create.repository')
                h.flash(_("Granted 'repository create' permission to user group"),
                        category='success')
            else:
                usergroup_model.revoke_perm(id, 'hg.create.repository')
                usergroup_model.grant_perm(id, 'hg.create.none')
                h.flash(_("Revoked 'repository create' permission to user group"),
                        category='success')

            if grant_fork_perm:
                usergroup_model.revoke_perm(id, 'hg.fork.none')
                usergroup_model.grant_perm(id, 'hg.fork.repository')
                h.flash(_("Granted 'repository fork' permission to user group"),
                        category='success')
            else:
                usergroup_model.revoke_perm(id, 'hg.fork.repository')
                usergroup_model.grant_perm(id, 'hg.fork.none')
                h.flash(_("Revoked 'repository fork' permission to user group"),
                        category='success')

            Session().commit()
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during permissions saving'),
                    category='error')

        return redirect(url('edit_users_group', id=id))
