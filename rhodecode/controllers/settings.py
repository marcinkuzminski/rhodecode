#!/usr/bin/env python
# encoding: utf-8
# settings controller for pylons
# Copyright (C) 2009-2010 Marcin Kuzminski <marcin@python-works.com>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License or (at your opinion) any later version of the license.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.
"""
Created on June 30, 2010
settings controller for pylons
@author: marcink
"""
from formencode import htmlfill
from pylons import tmpl_context as c, request, url
from pylons.controllers.util import redirect
from pylons.i18n.translation import _
from rhodecode.lib.auth import LoginRequired, HasRepoPermissionAllDecorator
from rhodecode.lib.base import BaseController, render
from rhodecode.lib.utils import invalidate_cache, action_logger
from rhodecode.model.forms import RepoSettingsForm, RepoForkForm
from rhodecode.model.repo import RepoModel
import formencode
import logging
import rhodecode.lib.helpers as h
import traceback

log = logging.getLogger(__name__)

class SettingsController(BaseController):

    @LoginRequired()
    @HasRepoPermissionAllDecorator('repository.admin')
    def __before__(self):
        super(SettingsController, self).__before__()

    def index(self, repo_name):
        repo_model = RepoModel()
        c.repo_info = repo = repo_model.get(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was created or renamed from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('home'))
        defaults = c.repo_info.__dict__
        defaults.update({'user':c.repo_info.user.username})
        c.users_array = repo_model.get_users_js()

        for p in c.repo_info.repo_to_perm:
            defaults.update({'perm_%s' % p.user.username:
                             p.permission.permission_name})

        return htmlfill.render(
            render('settings/repo_settings.html'),
            defaults=defaults,
            encoding="UTF-8",
            force_defaults=False
        )

    def update(self, repo_name):
        repo_model = RepoModel()
        changed_name = repo_name
        _form = RepoSettingsForm(edit=True, old_data={'repo_name':repo_name})()
        try:
            form_result = _form.to_python(dict(request.POST))
            repo_model.update(repo_name, form_result)
            invalidate_cache('cached_repo_list')
            h.flash(_('Repository %s updated successfully' % repo_name),
                    category='success')
            changed_name = form_result['repo_name']
        except formencode.Invalid, errors:
            c.repo_info = repo_model.get(repo_name)
            c.users_array = repo_model.get_users_js()
            errors.value.update({'user':c.repo_info.user.username})
            return htmlfill.render(
                render('settings/repo_settings.html'),
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        except Exception:
            log.error(traceback.format_exc())
            h.flash(_('error occured during update of repository %s') \
                    % repo_name, category='error')

        return redirect(url('repo_settings_home', repo_name=changed_name))



    def delete(self, repo_name):
        """DELETE /repos/repo_name: Delete an existing item"""
        # Forms posted to this method should contain a hidden field:
        #    <input type="hidden" name="_method" value="DELETE" />
        # Or using helpers:
        #    h.form(url('repo_settings_delete', repo_name=ID),
        #           method='delete')
        # url('repo_settings_delete', repo_name=ID)

        repo_model = RepoModel()
        repo = repo_model.get(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was moved or renamed  from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('home'))
        try:
            action_logger(self.rhodecode_user, 'user_deleted_repo',
                              repo_name, '', self.sa)
            repo_model.delete(repo)
            invalidate_cache('cached_repo_list')
            h.flash(_('deleted repository %s') % repo_name, category='success')
        except Exception:
            h.flash(_('An error occurred during deletion of %s') % repo_name,
                    category='error')

        return redirect(url('home'))

    def fork(self, repo_name):
        repo_model = RepoModel()
        c.repo_info = repo = repo_model.get(repo_name)
        if not repo:
            h.flash(_('%s repository is not mapped to db perhaps'
                      ' it was created or renamed from the filesystem'
                      ' please run the application again'
                      ' in order to rescan repositories') % repo_name,
                      category='error')

            return redirect(url('home'))

        return render('settings/repo_fork.html')



    def fork_create(self, repo_name):
        repo_model = RepoModel()
        c.repo_info = repo_model.get(repo_name)
        _form = RepoForkForm(old_data={'repo_type':c.repo_info.repo_type})()
        form_result = {}
        try:
            form_result = _form.to_python(dict(request.POST))
            form_result.update({'repo_name':repo_name})
            repo_model.create_fork(form_result, c.rhodecode_user)
            h.flash(_('fork %s repository as %s task added') \
                      % (repo_name, form_result['fork_name']),
                    category='success')
            action_logger(self.rhodecode_user, 'user_forked_repo',
                            repo_name, '', self.sa)
        except formencode.Invalid, errors:
            c.new_repo = errors.value['fork_name']
            r = render('settings/repo_fork.html')

            return htmlfill.render(
                r,
                defaults=errors.value,
                errors=errors.error_dict or {},
                prefix_error=False,
                encoding="UTF-8")
        return redirect(url('home'))
