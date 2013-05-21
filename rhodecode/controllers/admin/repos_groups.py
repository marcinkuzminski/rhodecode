# -*- coding: utf-8 -*-
"""
    rhodecode.controllers.admin.repos_groups
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Repository groups controller for RhodeCode

    :created_on: Mar 23, 2010
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

from pylons import request, tmpl_context as c, url
from pylons.controllers.util import abort, redirect
from pylons.i18n.translation import _

from sqlalchemy.exc import IntegrityError

import rhodecode
from rhodecode.lib import helpers as h
from rhodecode.lib.compat import json
from rhodecode.lib.auth import LoginRequired, HasPermissionAnyDecorator,\
    HasReposGroupPermissionAnyDecorator, HasReposGroupPermissionAll,\
    HasPermissionAll
from rhodecode.lib.base import BaseController, render
from rhodecode.model.db import RepoGroup, Repository
from rhodecode.model.scm import RepoGroupList
from rhodecode.model.repos_group import ReposGroupModel
from rhodecode.model.forms import ReposGroupForm, RepoGroupPermsForm
from rhodecode.model.meta import Session
from rhodecode.model.repo import RepoModel
from webob.exc import HTTPInternalServerError, HTTPNotFound
from rhodecode.lib.utils2 import str2bool, safe_int
from sqlalchemy.sql.expression import func


log = logging.getLogger(__name__)


class ReposGroupsController(BaseController):
    """REST Controller styled on the Atom Publishing Protocol"""
    # To properly map this controller, ensure your config/routing.py
    # file has a resource setup:
    #     map.resource('repos_group', 'repos_groups')

    @LoginRequired()
    def __before__(self):
        super(ReposGroupsController, self).__before__()

    def __load_defaults(self, allow_empty_group=False, exclude_group_ids=[]):
        if HasPermissionAll('hg.admin')('group edit'):
            #we're global admin, we're ok and we can create TOP level groups
            allow_empty_group = True

        #override the choices for this form, we need to filter choices
        #and display only those we have ADMIN right
        groups_with_admin_rights = RepoGroupList(RepoGroup.query().all(),
                                             perm_set=['group.admin'])
        c.repo_groups = RepoGroup.groups_choices(groups=groups_with_admin_rights,
                                                 show_empty_group=allow_empty_group)
        # exclude filtered ids
        c.repo_groups = filter(lambda x: x[0] not in exclude_group_ids,
                               c.repo_groups)
        c.repo_groups_choices = map(lambda k: unicode(k[0]), c.repo_groups)
        repo_model = RepoModel()
        c.users_array = repo_model.get_users_js()
        c.users_groups_array = repo_model.get_users_groups_js()

    def __load_data(self, group_id):
        """
        Load defaults settings for edit, and update

        :param group_id:
        """
        repo_group = RepoGroup.get_or_404(group_id)
        data = repo_group.get_dict()
        data['group_name'] = repo_group.name

        # fill repository group users
        for p in repo_group.repo_group_to_perm:
            data.update({'u_perm_%s' % p.user.username:
                             p.permission.permission_name})

        # fill repository group groups
        for p in repo_group.users_group_to_perm:
            data.update({'g_perm_%s' % p.users_group.users_group_name:
                             p.permission.permission_name})

        return data

    def _revoke_perms_on_yourself(self, form_result):
        _up = filter(lambda u: c.rhodecode_user.username == u[0],
                     form_result['perms_updates'])
        _new = filter(lambda u: c.rhodecode_user.username == u[0],
                      form_result['perms_new'])
        if _new and _new[0][1] != 'group.admin' or _up and _up[0][1] != 'group.admin':
            return True
        return False

    def index(self, format='html'):
        """GET /repos_groups: All items in the collection"""
        # url('repos_groups')
        group_iter = RepoGroupList(RepoGroup.query().all(),
                                   perm_set=['group.admin'])
        sk = lambda g: g.parents[0].group_name if g.parents else g.group_name
        c.groups = sorted(group_iter, key=sk)
        return render('admin/repos_groups/repos_groups_show.html')

    def create(self):
        """POST /repos_groups: Create a new item"""
        # url('repos_groups')

        self.__load_defaults()

        # permissions for can create group based on parent_id are checked
        # here in the Form
        repos_group_form = ReposGroupForm(available_groups=
                                map(lambda k: unicode(k[0]), c.repo_groups))()
        try:
            form_result = repos_group_form.to_python(dict(request.POST))
            ReposGroupModel().create(
                    group_name=form_result['group_name'],
                    group_description=form_result['group_description'],
                    parent=form_result['group_parent_id'],
                    owner=self.rhodecode_user.user_id
            )
            Session().commit()
            h.flash(_('Created repository group %s') \
                    % form_result['group_name'], category='success')
            #TODO: in futureaction_logger(, '', '', '', self.sa)
        except formencode.Invalid, errors:
            return htmlfill.render(
                render('admin/repos_groups/repos_groups_add.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('Error occurred during creation of repository group %s') \
                    % request.POST.get('group_name'), category='error')
        parent_group_id = form_result['group_parent_id']
        #TODO: maybe we should get back to the main view, not the admin one
        return redirect(url('repos_groups', parent_group=parent_group_id))

    def new(self, format='html'):
        """GET /repos_groups/new: Form to create a new item"""
        # url('new_repos_group')
        if HasPermissionAll('hg.admin')('group create'):
            #we're global admin, we're ok and we can create TOP level groups
            pass
        else:
            # we pass in parent group into creation form, thus we know
            # what would be the group, we can check perms here !
            group_id = safe_int(request.GET.get('parent_group'))
            group = RepoGroup.get(group_id) if group_id else None
            group_name = group.group_name if group else None
            if HasReposGroupPermissionAll('group.admin')(group_name, 'group create'):
                pass
            else:
                return abort(403)

        self.__load_defaults()
        return render('admin/repos_groups/repos_groups_add.html')

    @HasReposGroupPermissionAnyDecorator('group.admin')
    def update(self, group_name):
        """PUT /repos_groups/group_name: Update an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="PUT" />
        # Or using helpers:
        #    h.form(url('repos_group', group_name=GROUP_NAME),
        #           method='put')
        # url('repos_group', group_name=GROUP_NAME)

        c.repos_group = ReposGroupModel()._get_repo_group(group_name)
        if HasPermissionAll('hg.admin')('group edit'):
            #we're global admin, we're ok and we can create TOP level groups
            allow_empty_group = True
        elif not c.repos_group.parent_group:
            allow_empty_group = True
        else:
            allow_empty_group = False
        self.__load_defaults(allow_empty_group=allow_empty_group,
                             exclude_group_ids=[c.repos_group.group_id])

        repos_group_form = ReposGroupForm(
            edit=True,
            old_data=c.repos_group.get_dict(),
            available_groups=c.repo_groups_choices,
            can_create_in_root=allow_empty_group,
        )()
        try:
            form_result = repos_group_form.to_python(dict(request.POST))

            new_gr = ReposGroupModel().update(group_name, form_result)
            Session().commit()
            h.flash(_('Updated repository group %s') \
                    % form_result['group_name'], category='success')
            # we now have new name !
            group_name = new_gr.group_name
            #TODO: in future action_logger(, '', '', '', self.sa)
        except formencode.Invalid, errors:

            return htmlfill.render(
                render('admin/repos_groups/repos_groups_edit.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('Error occurred during update of repository group %s') \
                    % request.POST.get('group_name'), category='error')

        return redirect(url('edit_repos_group', group_name=group_name))

    @HasReposGroupPermissionAnyDecorator('group.admin')
    def delete(self, group_name):
        """DELETE /repos_groups/group_name: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repos_group', group_name=GROUP_NAME),
        #           method='delete')
        # url('repos_group', group_name=GROUP_NAME)

        gr = c.repos_group = ReposGroupModel()._get_repo_group(group_name)
        repos = gr.repositories.all()
        if repos:
            h.flash(_('This group contains %s repositores and cannot be '
                      'deleted') % len(repos), category='warning')
            return redirect(url('repos_groups'))

        children = gr.children.all()
        if children:
            h.flash(_('This group contains %s subgroups and cannot be deleted'
                      % (len(children))), category='warning')
            return redirect(url('repos_groups'))

        try:
            ReposGroupModel().delete(group_name)
            Session().commit()
            h.flash(_('Removed repository group %s') % group_name,
                    category='success')
            #TODO: in future action_logger(, '', '', '', self.sa)
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('Error occurred during deletion of repos '
                      'group %s') % group_name, category='error')

        return redirect(url('repos_groups'))

    @HasReposGroupPermissionAnyDecorator('group.admin')
    def set_repo_group_perm_member(self, group_name):
        c.repos_group = ReposGroupModel()._get_repo_group(group_name)
        form_result = RepoGroupPermsForm()().to_python(request.POST)
        if not c.rhodecode_user.is_admin:
            if self._revoke_perms_on_yourself(form_result):
                msg = _('Cannot revoke permission for yourself as admin')
                h.flash(msg, category='warning')
                return redirect(url('edit_repos_group', group_name=group_name))
        recursive = form_result['recursive']
        # iterate over all members(if in recursive mode) of this groups and
        # set the permissions !
        # this can be potentially heavy operation
        ReposGroupModel()._update_permissions(c.repos_group,
                                              form_result['perms_new'],
                                              form_result['perms_updates'],
                                              recursive)
        #TODO: implement this
        #action_logger(self.rhodecode_user, 'admin_changed_repo_permissions',
        #              repo_name, self.ip_addr, self.sa)
        Session().commit()
        h.flash(_('Repository Group permissions updated'), category='success')
        return redirect(url('edit_repos_group', group_name=group_name))

    @HasReposGroupPermissionAnyDecorator('group.admin')
    def delete_repo_group_perm_member(self, group_name):
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
            recursive = str2bool(request.POST.get('recursive', False))
            if obj_type == 'user':
                ReposGroupModel().delete_permission(
                    repos_group=group_name, obj=obj_id,
                    obj_type='user', recursive=recursive
                )
            elif obj_type == 'user_group':
                ReposGroupModel().delete_permission(
                    repos_group=group_name, obj=obj_id,
                    obj_type='users_group', recursive=recursive
                )

            Session().commit()
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('An error occurred during revoking of permission'),
                    category='error')
            raise HTTPInternalServerError()

    def show_by_name(self, group_name):
        """
        This is a proxy that does a lookup group_name -> id, and shows
        the group by id view instead
        """
        group_name = group_name.rstrip('/')
        id_ = RepoGroup.get_by_group_name(group_name)
        if id_:
            return self.show(id_.group_id)
        raise HTTPNotFound

    @HasReposGroupPermissionAnyDecorator('group.read', 'group.write',
                                         'group.admin')
    def show(self, group_name, format='html'):
        """GET /repos_groups/group_name: Show a specific item"""
        # url('repos_group', group_name=GROUP_NAME)

        c.group = c.repos_group = ReposGroupModel()._get_repo_group(group_name)
        c.group_repos = c.group.repositories.all()

        #overwrite our cached list with current filter
        gr_filter = c.group_repos
        c.repo_cnt = 0

        groups = RepoGroup.query().order_by(RepoGroup.group_name)\
            .filter(RepoGroup.group_parent_id == c.group.group_id).all()
        c.groups = self.scm_model.get_repos_groups(groups)

        c.repos_list = Repository.query()\
                        .filter(Repository.group_id == c.group.group_id)\
                        .order_by(func.lower(Repository.repo_name))\
                        .all()

        repos_data = RepoModel().get_repos_as_dict(repos_list=c.repos_list,
                                                   admin=False)
        #json used to render the grid
        c.data = json.dumps(repos_data)

        return render('admin/repos_groups/repos_groups.html')

    @HasReposGroupPermissionAnyDecorator('group.admin')
    def edit(self, group_name, format='html'):
        """GET /repos_groups/group_name/edit: Form to edit an existing item"""
        # url('edit_repos_group', group_name=GROUP_NAME)

        c.repos_group = ReposGroupModel()._get_repo_group(group_name)
        #we can only allow moving empty group if it's already a top-level
        #group, ie has no parents, or we're admin
        if HasPermissionAll('hg.admin')('group edit'):
            #we're global admin, we're ok and we can create TOP level groups
            allow_empty_group = True
        elif not c.repos_group.parent_group:
            allow_empty_group = True
        else:
            allow_empty_group = False

        self.__load_defaults(allow_empty_group=allow_empty_group,
                             exclude_group_ids=[c.repos_group.group_id])
        defaults = self.__load_data(c.repos_group.group_id)

        return htmlfill.render(
            render('admin/repos_groups/repos_groups_edit.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )
