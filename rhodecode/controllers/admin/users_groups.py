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
from rhodecode.lib.exceptions import UserGroupsAssignedException,\
    RepoGroupAssignmentError
from rhodecode.lib.utils2 import safe_unicode, str2bool, safe_int
from rhodecode.lib.auth import LoginRequired, HasPermissionAllDecorator,\
    HasUserGroupPermissionAnyDecorator, HasPermissionAnyDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.model.scm import UserGroupList
from rhodecode.model.users_group import UserGroupModel
from rhodecode.model.repo import RepoModel
from rhodecode.model.db import User, UserGroup, UserGroupToPerm,\
    UserGroupRepoToPerm, UserGroupRepoGroupToPerm
from rhodecode.model.forms import UserGroupForm, UserGroupPermsForm,\
    CustomDefaultPermissionsForm
from rhodecode.model.meta import Session
from rhodecode.lib.utils import action_logger
from sqlalchemy.orm import joinedload
from webob.exc import HTTPInternalServerError

log = logging.getLogger(__name__)


class UsersGroupsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('users_group', 'users_groups')

    @LoginRequired()
    def __before__(self):
        super(UsersGroupsController, self).__before__()
        c.available_permissions = config['available_permissions']

    def __load_data(self, user_group_id):
        ugroup_repo_perms = UserGroupRepoToPerm.query()\
            .options(joinedload(UserGroupRepoToPerm.permission))\
            .options(joinedload(UserGroupRepoToPerm.repository))\
            .filter(UserGroupRepoToPerm.users_group_id == user_group_id)\
            .all()

        for gr in ugroup_repo_perms:
            c.users_group.permissions['repositories'][gr.repository.repo_name]  \
                = gr.permission.permission_name

        ugroup_group_perms = UserGroupRepoGroupToPerm.query()\
            .options(joinedload(UserGroupRepoGroupToPerm.permission))\
            .options(joinedload(UserGroupRepoGroupToPerm.group))\
            .filter(UserGroupRepoGroupToPerm.users_group_id == user_group_id)\
            .all()

        for gr in ugroup_group_perms:
            c.users_group.permissions['repositories_groups'][gr.group.group_name] \
                = gr.permission.permission_name

        c.group_members_obj = sorted((x.user for x in c.users_group.members),
                                     key=lambda u: u.username.lower())

        c.group_members = [(x.user_id, x.username) for x in c.group_members_obj]
        c.available_members = sorted(((x.user_id, x.username) for x in
                                      User.query().all()),
                                     key=lambda u: u[1].lower())
        repo_model = RepoModel()
        c.users_array = repo_model.get_users_js()
        c.users_groups_array = repo_model.get_users_groups_js()
        c.available_permissions = config['available_permissions']

    def __load_defaults(self, user_group_id):
        """
        Load defaults settings for edit, and update

        :param user_group_id:
        """
        user_group = UserGroup.get_or_404(user_group_id)
        data = user_group.get_dict()

        ug_model = UserGroupModel()

        data.update({
            'create_repo_perm': ug_model.has_perm(user_group,
                                                  'hg.create.repository'),
            'create_user_group_perm': ug_model.has_perm(user_group,
                                                  'hg.usergroup.create.true'),
            'fork_repo_perm': ug_model.has_perm(user_group,
                                                'hg.fork.repository'),
        })

        # fill user group users
        for p in user_group.user_user_group_to_perm:
            data.update({'u_perm_%s' % p.user.username:
                             p.permission.permission_name})

        for p in user_group.user_group_user_group_to_perm:
            data.update({'g_perm_%s' % p.user_group.users_group_name:
                             p.permission.permission_name})

        return data

    def index(self, format='html'):
        """GET /users_groups: All items in the collection"""
        # url('users_groups')

        group_iter = UserGroupList(UserGroup().query().all(),
                                   perm_set=['usergroup.admin'])
        sk = lambda g: g.users_group_name
        c.users_groups_list = sorted(group_iter, key=sk)
        return render('admin/users_groups/users_groups.html')

    @HasPermissionAnyDecorator('hg.admin', 'hg.usergroup.create.true')
    def create(self):
        """POST /users_groups: Create a new item"""
        # url('users_groups')

        users_group_form = UserGroupForm()()
        try:
            form_result = users_group_form.to_python(dict(request.POST))
            UserGroupModel().create(name=form_result['users_group_name'],
                                    owner=self.rhodecode_user.user_id,
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

    @HasPermissionAnyDecorator('hg.admin', 'hg.usergroup.create.true')
    def new(self, format='html'):
        """GET /users_groups/new: Form to create a new item"""
        # url('new_users_group')
        return render('admin/users_groups/users_group_add.html')

    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    def update(self, id):
        """PUT /users_groups/id: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('users_group', id=ID),
        #           method='put')
        # url('users_group', id=ID)

        c.users_group = UserGroup.get_or_404(id)
        self.__load_data(id)

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

    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
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

    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    def set_user_group_perm_member(self, id):
        """
        grant permission for given usergroup

        :param id:
        """
        user_group = UserGroup.get_or_404(id)
        form = UserGroupPermsForm()().to_python(request.POST)

        # set the permissions !
        try:
            UserGroupModel()._update_permissions(user_group, form['perms_new'],
                                                 form['perms_updates'])
        except RepoGroupAssignmentError:
            h.flash(_('Target group cannot be the same'), category='error')
            return redirect(url('edit_users_group', id=id))
        #TODO: implement this
        #action_logger(self.rhodecode_user, 'admin_changed_repo_permissions',
        #              repo_name, self.ip_addr, self.sa)
        Session().commit()
        h.flash(_('User Group permissions updated'), category='success')
        return redirect(url('edit_users_group', id=id))

    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    def delete_user_group_perm_member(self, id):
        """
        DELETE an existing repository group permission user

        :param group_name:
        """
        try:
            obj_type = request.POST.get('obj_type')
            obj_id = None
            if obj_type == 'user':
                obj_id = safe_int(request.POST.get('user_id'))
            elif obj_type == 'user_group':
                obj_id = safe_int(request.POST.get('user_group_id'))

            if not c.rhodecode_user.is_admin:
                if obj_type == 'user' and c.rhodecode_user.user_id == obj_id:
                    msg = _('Cannot revoke permission for yourself as admin')
                    h.flash(msg, category='warning')
                    raise Exception('revoke admin permission on self')
            if obj_type == 'user':
                UserGroupModel().revoke_user_permission(user_group=id,
                                                        user=obj_id)
            elif obj_type == 'user_group':
                UserGroupModel().revoke_users_group_permission(target_user_group=id,
                                                               user_group=obj_id)
            Session().commit()
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during revoking of permission'),
                    category='error')
            raise HTTPInternalServerError()

    def show(self, id, format='html'):
        """GET /users_groups/id: Show a specific item"""
        # url('users_group', id=ID)

    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    def edit(self, id, format='html'):
        """GET /users_groups/id/edit: Form to edit an existing item"""
        # url('edit_users_group', id=ID)

        c.users_group = UserGroup.get_or_404(id)
        self.__load_data(id)

        defaults = self.__load_defaults(id)

        return htmlfill.render(
            render('admin/users_groups/users_group_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    @HasUserGroupPermissionAnyDecorator('usergroup.admin')
    def update_perm(self, id):
        """PUT /users_perm/id: Update an existing item"""
        # url('users_group_perm', id=ID, method='put')

        users_group = UserGroup.get_or_404(id)

        try:
            form = CustomDefaultPermissionsForm()()
            form_result = form.to_python(request.POST)

            inherit_perms = form_result['inherit_default_permissions']
            users_group.inherit_default_permissions = inherit_perms
            Session().add(users_group)
            usergroup_model = UserGroupModel()

            defs = UserGroupToPerm.query()\
                .filter(UserGroupToPerm.users_group == users_group)\
                .all()
            for ug in defs:
                Session().delete(ug)

            if form_result['create_repo_perm']:
                usergroup_model.grant_perm(id, 'hg.create.repository')
            else:
                usergroup_model.grant_perm(id, 'hg.create.none')
            if form_result['create_user_group_perm']:
                usergroup_model.grant_perm(id, 'hg.usergroup.create.true')
            else:
                usergroup_model.grant_perm(id, 'hg.usergroup.create.false')
            if form_result['fork_repo_perm']:
                usergroup_model.grant_perm(id, 'hg.fork.repository')
            else:
                usergroup_model.grant_perm(id, 'hg.fork.none')

            h.flash(_("Updated permissions"), category='success')
            Session().commit()
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during permissions saving'),
                    category='error')

        return redirect(url('edit_users_group', id=id))
